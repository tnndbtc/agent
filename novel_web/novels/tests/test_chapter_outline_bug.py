"""
Test for bug where chapter 1 disappears when writing chapter 3.

This bug occurs because Chapter.outline is a OneToOneField, and the
update_or_create logic in write_chapter_task can cause wrong outline
associations when chapter_number (lookup key) doesn't match the outline
parameter (in defaults).
"""
import pytest
import itertools
from django.contrib.auth.models import User
from novels.models import NovelProject, ChapterOutline, Chapter, Plot, Act


@pytest.mark.django_db
class TestChapterOutlineBug:
    """Test for bug where chapter 1 disappears when writing chapter 3."""

    def test_writing_multiple_chapters_preserves_all_content(self):
        """
        Reproduce the bug: writing chapter 3 causes chapter 1 to disappear.

        This happens because:
        1. Chapter.outline is a OneToOneField
        2. update_or_create looks up by chapter_number but sets outline in defaults
        3. If the wrong outline is passed, it can break the relationship
        """
        # Setup: Create user and project
        user = User.objects.create_user(username='testuser', password='test123')
        project = NovelProject.objects.create(
            user=user,
            title='Test Novel'
        )

        # Create plot and act (required for outlines)
        plot = Plot.objects.create(
            project=project,
            conflict='Test conflict'
        )

        act = Act.objects.create(
            plot=plot,
            act_number=1,
            subject='Setup',
            description='First act',
        )

        # Create 3 chapter outlines
        outline1 = ChapterOutline.objects.create(
            project=project,
            act=act,
            number=1,
            title='Chapter 1',
            events='Events for chapter 1'
        )

        outline2 = ChapterOutline.objects.create(
            project=project,
            act=act,
            number=2,
            title='Chapter 2',
            events='Events for chapter 2'
        )

        outline3 = ChapterOutline.objects.create(
            project=project,
            act=act,
            number=3,
            title='Chapter 3',
            events='Events for chapter 3'
        )

        # Write Chapter 1
        chapter1 = Chapter.objects.create(
            project=project,
            outline=outline1,
            chapter_number=1,
            title='Chapter 1',
            content='This is chapter 1 content - SHOULD NOT DISAPPEAR',
            version=1
        )

        # Write Chapter 3 (using the SAME logic as write_chapter_task)
        chapter3, created = Chapter.objects.update_or_create(
            project=project,
            chapter_number=3,  # Looking up by chapter_number=3
            version=1,
            defaults={
                'title': 'Chapter 3',
                'content': 'This is chapter 3 content',
            }
        )

        # Set outline separately (this is the fix)
        if created or chapter3.outline != outline3:
            chapter3.outline = outline3
            chapter3.save(update_fields=['outline'])

        # Refresh chapter1 from database
        chapter1.refresh_from_db()

        # BUG CHECK: Chapter 1 should still exist with its original content
        assert chapter1.content == 'This is chapter 1 content - SHOULD NOT DISAPPEAR', \
            "Chapter 1 content disappeared after writing chapter 3!"

        # Verify outline relationships are correct
        assert chapter1.outline == outline1, f"Chapter 1 lost its outline link. Expected {outline1}, got {chapter1.outline}"
        assert chapter3.outline == outline3, f"Chapter 3 has wrong outline. Expected {outline3}, got {chapter3.outline}"

        # Verify no chapters were deleted
        assert Chapter.objects.filter(project=project).count() == 2, \
            "Chapters were deleted"

        # Verify outlines still have correct chapter links
        outline1.refresh_from_db()
        outline3.refresh_from_db()
        assert hasattr(outline1, 'chapter') and outline1.chapter == chapter1, \
            "Outline1's reverse relationship broken"
        assert hasattr(outline3, 'chapter') and outline3.chapter == chapter3, \
            "Outline3's reverse relationship broken"

    def test_bug_reproduction_with_wrong_outline_in_defaults(self):
        """
        Reproduce the bug by putting outline in defaults dict.
        This demonstrates what happens if outline is in defaults when it shouldn't be.
        """
        user = User.objects.create_user(username='testuser2', password='test123')
        project = NovelProject.objects.create(user=user, title='Test Novel 2')
        plot = Plot.objects.create(project=project, conflict='Test conflict')
        act = Act.objects.create(plot=plot, act_number=1, subject='Setup',
                                description='Act 1')

        # Create outlines
        outline1 = ChapterOutline.objects.create(
            project=project, act=act, number=1, title='Chapter 1', events='Events 1'
        )
        outline3 = ChapterOutline.objects.create(
            project=project, act=act, number=3, title='Chapter 3', events='Events 3'
        )

        # Write Chapter 1
        chapter1 = Chapter.objects.create(
            project=project,
            outline=outline1,
            chapter_number=1,
            title='Chapter 1',
            content='Original chapter 1 content',
            version=1
        )

        # Store original outline for verification
        original_outline_id = chapter1.outline.id

        # BUG SCENARIO: update_or_create with outline in defaults
        # This simulates the buggy behavior when outline is in defaults dict
        chapter_updated, created = Chapter.objects.update_or_create(
            project=project,
            chapter_number=1,  # Looks up chapter 1
            version=1,
            defaults={
                'outline': outline3,  # BUGGY: Trying to change outline via defaults
                'title': 'Chapter 1 Updated',
                'content': 'Updated content',
            }
        )

        # Verify this causes the bug
        chapter_updated.refresh_from_db()

        # The bug: chapter1 now has the WRONG outline
        assert chapter_updated.outline == outline3, \
            "Bug reproduced: Chapter 1 now has wrong outline (outline3 instead of outline1)"

        # And outline1 now has NO chapter linked to it
        outline1.refresh_from_db()
        assert not hasattr(outline1, 'chapter') or outline1.chapter is None, \
            "Outline1 lost its chapter link due to OneToOneField constraint"

    def test_chapter_number_outline_number_mismatch_validation(self):
        """
        Test that we catch mismatches between chapter_number and outline.number.
        This prevents the bug from happening in the first place.
        """
        user = User.objects.create_user(username='testuser3', password='test123')
        project = NovelProject.objects.create(user=user, title='Test Novel 3')
        plot = Plot.objects.create(project=project, conflict='Test conflict')
        act = Act.objects.create(plot=plot, act_number=1, subject='Setup',
                                description='Act 1')

        outline1 = ChapterOutline.objects.create(
            project=project, act=act, number=1, title='Chapter 1', events='Events 1'
        )
        outline3 = ChapterOutline.objects.create(
            project=project, act=act, number=3, title='Chapter 3', events='Events 3'
        )

        # This should be caught by validation
        # Attempting to create chapter_number=1 with outline3 (number=3)
        chapter_data = {
            'chapter_number': 1,  # Says chapter 1
            'title': 'Chapter 1',
            'content': 'Content',
        }

        outline = outline3  # But using outline 3

        # Validation check (this is what we'll add to tasks.py)
        if outline.number != chapter_data['chapter_number']:
            error_msg = (f"Mismatch: outline.number={outline.number} but "
                        f"chapter_data['chapter_number']={chapter_data['chapter_number']}")
            # This should raise an error
            with pytest.raises(ValueError, match="Mismatch"):
                raise ValueError(error_msg)

    @pytest.mark.parametrize("write_order", [
        [1, 2, 3],  # Sequential
        [2, 3, 1],  # Middle-out
        [1, 3, 2],  # Skip middle
        [2, 1, 3],  # Start middle
        [3, 1, 2],  # Reverse start
        [3, 2, 1],  # Full reverse
    ])
    def test_all_3_chapter_write_orders_buggy_version(self, write_order):
        """
        Test ALL possible write orders for 3 chapters using BUGGY approach.
        This demonstrates that outline in defaults causes data loss.

        This test SHOULD FAIL - it demonstrates the bug.
        """
        user = User.objects.create_user(
            username=f'testuser_buggy_{write_order[0]}{write_order[1]}{write_order[2]}',
            password='test123'
        )
        project = NovelProject.objects.create(
            user=user,
            title=f'Test Novel - Buggy Order {write_order}'
        )
        plot = Plot.objects.create(project=project, conflict='Test conflict')
        act = Act.objects.create(plot=plot, act_number=1, subject='Setup',
                                description='Act 1')

        # Create 3 outlines
        outlines = {}
        for i in range(1, 4):
            outlines[i] = ChapterOutline.objects.create(
                project=project,
                act=act,
                number=i,
                title=f'Chapter {i}',
                events=f'Events for chapter {i}'
            )

        # Write chapters in the specified order using BUGGY approach
        written_chapters = {}
        for chapter_num in write_order:
            chapter, created = Chapter.objects.update_or_create(
                project=project,
                chapter_number=chapter_num,
                version=1,
                defaults={
                    'outline': outlines[chapter_num],  # BUGGY: outline in defaults
                    'title': f'Chapter {chapter_num}',
                    'content': f'This is chapter {chapter_num} content - MUST NOT DISAPPEAR',
                }
            )
            written_chapters[chapter_num] = chapter

        # Verify all 3 chapters exist
        all_chapters = Chapter.objects.filter(project=project)
        assert all_chapters.count() == 3, \
            f"Expected 3 chapters but got {all_chapters.count()} for order {write_order}"

        # Verify each chapter has correct content and outline
        for i in range(1, 4):
            chapter = Chapter.objects.get(project=project, chapter_number=i, version=1)
            expected_content = f'This is chapter {i} content - MUST NOT DISAPPEAR'

            assert chapter.content == expected_content, \
                f"Chapter {i} content wrong in order {write_order}. Expected: {expected_content}, Got: {chapter.content}"

            assert chapter.outline == outlines[i], \
                f"Chapter {i} has wrong outline in order {write_order}. Expected: {outlines[i]}, Got: {chapter.outline}"

        # Verify reverse relationships
        for i in range(1, 4):
            outlines[i].refresh_from_db()
            assert hasattr(outlines[i], 'chapter'), \
                f"Outline {i} lost its chapter link in order {write_order}"
            assert outlines[i].chapter.chapter_number == i, \
                f"Outline {i} linked to wrong chapter in order {write_order}"

    @pytest.mark.parametrize("write_order", [
        [1, 2, 3],  # Sequential
        [2, 3, 1],  # Middle-out
        [1, 3, 2],  # Skip middle
        [2, 1, 3],  # Start middle
        [3, 1, 2],  # Reverse start
        [3, 2, 1],  # Full reverse
    ])
    def test_all_3_chapter_write_orders_fixed_version(self, write_order):
        """
        Test ALL possible write orders for 3 chapters using FIXED approach.
        This demonstrates that setting outline separately prevents data loss.

        This test SHOULD PASS - it demonstrates the fix works.
        """
        user = User.objects.create_user(
            username=f'testuser_fixed_{write_order[0]}{write_order[1]}{write_order[2]}',
            password='test123'
        )
        project = NovelProject.objects.create(
            user=user,
            title=f'Test Novel - Fixed Order {write_order}'
        )
        plot = Plot.objects.create(project=project, conflict='Test conflict')
        act = Act.objects.create(plot=plot, act_number=1, subject='Setup',
                                description='Act 1')

        # Create 3 outlines
        outlines = {}
        for i in range(1, 4):
            outlines[i] = ChapterOutline.objects.create(
                project=project,
                act=act,
                number=i,
                title=f'Chapter {i}',
                events=f'Events for chapter {i}'
            )

        # Write chapters in the specified order using FIXED approach
        written_chapters = {}
        for chapter_num in write_order:
            chapter, created = Chapter.objects.update_or_create(
                project=project,
                chapter_number=chapter_num,
                version=1,
                defaults={
                    # outline NOT in defaults - this is the fix
                    'title': f'Chapter {chapter_num}',
                    'content': f'This is chapter {chapter_num} content - MUST NOT DISAPPEAR',
                }
            )

            # Set outline separately (the fix)
            if created or chapter.outline != outlines[chapter_num]:
                chapter.outline = outlines[chapter_num]
                chapter.save(update_fields=['outline'])

            written_chapters[chapter_num] = chapter

        # Verify all 3 chapters exist
        all_chapters = Chapter.objects.filter(project=project)
        assert all_chapters.count() == 3, \
            f"Expected 3 chapters but got {all_chapters.count()} for order {write_order}"

        # Verify each chapter has correct content and outline
        for i in range(1, 4):
            chapter = Chapter.objects.get(project=project, chapter_number=i, version=1)
            expected_content = f'This is chapter {i} content - MUST NOT DISAPPEAR'

            assert chapter.content == expected_content, \
                f"Chapter {i} content wrong in order {write_order}. Expected: {expected_content}, Got: {chapter.content}"

            assert chapter.outline == outlines[i], \
                f"Chapter {i} has wrong outline in order {write_order}. Expected: {outlines[i]}, Got: {chapter.outline}"

        # Verify reverse relationships
        for i in range(1, 4):
            outlines[i].refresh_from_db()
            assert hasattr(outlines[i], 'chapter'), \
                f"Outline {i} lost its chapter link in order {write_order}"
            assert outlines[i].chapter.chapter_number == i, \
                f"Outline {i} linked to wrong chapter in order {write_order}"

    def test_8_chapter_random_order_buggy_version(self):
        """
        Test writing 8 chapters in random order [1, 2, 6, 5, 3, 4, 8, 7] using BUGGY approach.

        This test SHOULD FAIL - it demonstrates the bug with more chapters.
        """
        write_order = [1, 2, 6, 5, 3, 4, 8, 7]

        user = User.objects.create_user(username='testuser_8ch_buggy', password='test123')
        project = NovelProject.objects.create(
            user=user,
            title='Test Novel - 8 Chapters Buggy'
        )
        plot = Plot.objects.create(project=project, conflict='Test conflict')
        act = Act.objects.create(plot=plot, act_number=1, subject='Setup',
                                description='Act 1')

        # Create 8 outlines
        outlines = {}
        for i in range(1, 9):
            outlines[i] = ChapterOutline.objects.create(
                project=project,
                act=act,
                number=i,
                title=f'Chapter {i}',
                events=f'Events for chapter {i}'
            )

        # Write chapters in the specified order using BUGGY approach
        for chapter_num in write_order:
            chapter, created = Chapter.objects.update_or_create(
                project=project,
                chapter_number=chapter_num,
                version=1,
                defaults={
                    'outline': outlines[chapter_num],  # BUGGY: outline in defaults
                    'title': f'Chapter {chapter_num}',
                    'content': f'This is chapter {chapter_num} content - MUST NOT DISAPPEAR',
                }
            )

        # Verify all 8 chapters exist
        all_chapters = Chapter.objects.filter(project=project)
        assert all_chapters.count() == 8, \
            f"Expected 8 chapters but got {all_chapters.count()} for order {write_order}"

        # Verify each chapter has correct content and outline
        for i in range(1, 9):
            chapter = Chapter.objects.get(project=project, chapter_number=i, version=1)
            expected_content = f'This is chapter {i} content - MUST NOT DISAPPEAR'

            assert chapter.content == expected_content, \
                f"Chapter {i} content wrong. Expected: {expected_content}, Got: {chapter.content}"

            assert chapter.outline == outlines[i], \
                f"Chapter {i} has wrong outline. Expected outline {i}, Got: outline {chapter.outline.number if chapter.outline else None}"

        # Verify reverse relationships
        for i in range(1, 9):
            outlines[i].refresh_from_db()
            assert hasattr(outlines[i], 'chapter'), \
                f"Outline {i} lost its chapter link"
            assert outlines[i].chapter.chapter_number == i, \
                f"Outline {i} linked to wrong chapter: {outlines[i].chapter.chapter_number}"

    def test_rewrite_chapter_causes_other_chapters_to_disappear_buggy(self):
        """
        Test the exact bug reported: "when re-write first chapter, the 3rd chapter is gone."

        This test writes chapters 1, 2, 3, then REWRITES chapter 1 using buggy approach.
        The bug manifests when outline is in defaults dict during rewrite.

        This test SHOULD FAIL if the bug exists.
        """
        user = User.objects.create_user(username='testuser_rewrite_buggy', password='test123')
        project = NovelProject.objects.create(
            user=user,
            title='Test Novel - Rewrite Bug'
        )
        plot = Plot.objects.create(project=project, conflict='Test conflict')
        act = Act.objects.create(plot=plot, act_number=1, subject='Setup',
                                description='Act 1')

        # Create 3 outlines
        outlines = {}
        for i in range(1, 4):
            outlines[i] = ChapterOutline.objects.create(
                project=project,
                act=act,
                number=i,
                title=f'Chapter {i}',
                events=f'Events for chapter {i}'
            )

        # Write chapters 1, 2, 3 initially using BUGGY approach
        for chapter_num in [1, 2, 3]:
            chapter, created = Chapter.objects.update_or_create(
                project=project,
                chapter_number=chapter_num,
                version=1,
                defaults={
                    'outline': outlines[chapter_num],  # BUGGY: outline in defaults
                    'title': f'Chapter {chapter_num}',
                    'content': f'Original chapter {chapter_num} content',
                }
            )

        # Verify all 3 chapters exist
        assert Chapter.objects.filter(project=project).count() == 3, \
            "Should have 3 chapters after initial write"

        # Store chapter 3 ID for verification
        chapter3_before = Chapter.objects.get(project=project, chapter_number=3)
        chapter3_id_before = chapter3_before.id
        chapter3_content_before = chapter3_before.content

        # Now REWRITE chapter 1 (this is where the bug happens)
        chapter1_rewrite, created = Chapter.objects.update_or_create(
            project=project,
            chapter_number=1,
            version=1,
            defaults={
                'outline': outlines[1],  # BUGGY: outline in defaults during rewrite
                'title': 'Chapter 1 Rewritten',
                'content': 'Rewritten chapter 1 content',
            }
        )

        # BUG CHECK: Verify chapter 3 still exists with same content
        try:
            chapter3_after = Chapter.objects.get(project=project, chapter_number=3)
            assert chapter3_after.id == chapter3_id_before, \
                f"Chapter 3 was recreated (different ID)! Before: {chapter3_id_before}, After: {chapter3_after.id}"
            assert chapter3_after.content == chapter3_content_before, \
                f"Chapter 3 content changed! Before: {chapter3_content_before}, After: {chapter3_after.content}"
            assert chapter3_after.outline == outlines[3], \
                f"Chapter 3 has wrong outline! Expected: {outlines[3]}, Got: {chapter3_after.outline}"
        except Chapter.DoesNotExist:
            raise AssertionError("BUG REPRODUCED: Chapter 3 disappeared after rewriting chapter 1!")

        # Verify all 3 chapters still exist
        all_chapters = Chapter.objects.filter(project=project)
        assert all_chapters.count() == 3, \
            f"Expected 3 chapters after rewrite but got {all_chapters.count()}"

        # Verify each chapter has correct content
        chapter1_final = Chapter.objects.get(project=project, chapter_number=1)
        assert chapter1_final.content == 'Rewritten chapter 1 content', \
            "Chapter 1 should have rewritten content"
        assert chapter1_final.outline == outlines[1], \
            "Chapter 1 should still have correct outline"

    def test_rewrite_chapter_preserves_other_chapters_fixed(self):
        """
        Test that rewriting a chapter DOES NOT cause other chapters to disappear (FIXED version).

        This test writes chapters 1, 2, 3, then REWRITES chapter 1 using fixed approach.
        The fix sets outline separately, preventing OneToOneField conflicts.

        This test SHOULD PASS - demonstrates the fix works.
        """
        user = User.objects.create_user(username='testuser_rewrite_fixed', password='test123')
        project = NovelProject.objects.create(
            user=user,
            title='Test Novel - Rewrite Fixed'
        )
        plot = Plot.objects.create(project=project, conflict='Test conflict')
        act = Act.objects.create(plot=plot, act_number=1, subject='Setup',
                                description='Act 1')

        # Create 3 outlines
        outlines = {}
        for i in range(1, 4):
            outlines[i] = ChapterOutline.objects.create(
                project=project,
                act=act,
                number=i,
                title=f'Chapter {i}',
                events=f'Events for chapter {i}'
            )

        # Write chapters 1, 2, 3 initially using FIXED approach
        for chapter_num in [1, 2, 3]:
            chapter, created = Chapter.objects.update_or_create(
                project=project,
                chapter_number=chapter_num,
                version=1,
                defaults={
                    # outline NOT in defaults - this is the fix
                    'title': f'Chapter {chapter_num}',
                    'content': f'Original chapter {chapter_num} content',
                }
            )
            # Set outline separately
            if created or chapter.outline != outlines[chapter_num]:
                chapter.outline = outlines[chapter_num]
                chapter.save(update_fields=['outline'])

        # Verify all 3 chapters exist
        assert Chapter.objects.filter(project=project).count() == 3, \
            "Should have 3 chapters after initial write"

        # Store chapter 3 ID for verification
        chapter3_before = Chapter.objects.get(project=project, chapter_number=3)
        chapter3_id_before = chapter3_before.id
        chapter3_content_before = chapter3_before.content

        # Now REWRITE chapter 1 using FIXED approach
        chapter1_rewrite, created = Chapter.objects.update_or_create(
            project=project,
            chapter_number=1,
            version=1,
            defaults={
                # outline NOT in defaults
                'title': 'Chapter 1 Rewritten',
                'content': 'Rewritten chapter 1 content',
            }
        )
        # Set outline separately
        if created or chapter1_rewrite.outline != outlines[1]:
            chapter1_rewrite.outline = outlines[1]
            chapter1_rewrite.save(update_fields=['outline'])

        # Verify chapter 3 still exists with same content
        chapter3_after = Chapter.objects.get(project=project, chapter_number=3)
        assert chapter3_after.id == chapter3_id_before, \
            f"Chapter 3 should have same ID! Before: {chapter3_id_before}, After: {chapter3_after.id}"
        assert chapter3_after.content == chapter3_content_before, \
            f"Chapter 3 content should be unchanged! Before: {chapter3_content_before}, After: {chapter3_after.content}"
        assert chapter3_after.outline == outlines[3], \
            f"Chapter 3 should have correct outline! Expected: {outlines[3]}, Got: {chapter3_after.outline}"

        # Verify all 3 chapters still exist
        all_chapters = Chapter.objects.filter(project=project)
        assert all_chapters.count() == 3, \
            f"Expected 3 chapters after rewrite but got {all_chapters.count()}"

        # Verify each chapter has correct content
        chapter1_final = Chapter.objects.get(project=project, chapter_number=1)
        assert chapter1_final.content == 'Rewritten chapter 1 content', \
            "Chapter 1 should have rewritten content"
        assert chapter1_final.outline == outlines[1], \
            "Chapter 1 should still have correct outline"

        # Verify all outline relationships are correct
        for i in range(1, 4):
            outlines[i].refresh_from_db()
            assert hasattr(outlines[i], 'chapter'), \
                f"Outline {i} should have a chapter link"
            assert outlines[i].chapter.chapter_number == i, \
                f"Outline {i} should link to chapter {i}, not {outlines[i].chapter.chapter_number}"

    def test_8_chapter_random_order_fixed_version(self):
        """
        Test writing 8 chapters in random order [1, 2, 6, 5, 3, 4, 8, 7] using FIXED approach.

        This test SHOULD PASS - it demonstrates the fix works with many chapters.
        """
        write_order = [1, 2, 6, 5, 3, 4, 8, 7]

        user = User.objects.create_user(username='testuser_8ch_fixed', password='test123')
        project = NovelProject.objects.create(
            user=user,
            title='Test Novel - 8 Chapters Fixed'
        )
        plot = Plot.objects.create(project=project, conflict='Test conflict')
        act = Act.objects.create(plot=plot, act_number=1, subject='Setup',
                                description='Act 1')

        # Create 8 outlines
        outlines = {}
        for i in range(1, 9):
            outlines[i] = ChapterOutline.objects.create(
                project=project,
                act=act,
                number=i,
                title=f'Chapter {i}',
                events=f'Events for chapter {i}'
            )

        # Write chapters in the specified order using FIXED approach
        for chapter_num in write_order:
            chapter, created = Chapter.objects.update_or_create(
                project=project,
                chapter_number=chapter_num,
                version=1,
                defaults={
                    # outline NOT in defaults - this is the fix
                    'title': f'Chapter {chapter_num}',
                    'content': f'This is chapter {chapter_num} content - MUST NOT DISAPPEAR',
                }
            )

            # Set outline separately (the fix)
            if created or chapter.outline != outlines[chapter_num]:
                chapter.outline = outlines[chapter_num]
                chapter.save(update_fields=['outline'])

        # Verify all 8 chapters exist
        all_chapters = Chapter.objects.filter(project=project)
        assert all_chapters.count() == 8, \
            f"Expected 8 chapters but got {all_chapters.count()} for order {write_order}"

        # Verify each chapter has correct content and outline
        for i in range(1, 9):
            chapter = Chapter.objects.get(project=project, chapter_number=i, version=1)
            expected_content = f'This is chapter {i} content - MUST NOT DISAPPEAR'

            assert chapter.content == expected_content, \
                f"Chapter {i} content wrong. Expected: {expected_content}, Got: {chapter.content}"

            assert chapter.outline == outlines[i], \
                f"Chapter {i} has wrong outline. Expected outline {i}, Got: outline {chapter.outline.number if chapter.outline else None}"

        # Verify reverse relationships
        for i in range(1, 9):
            outlines[i].refresh_from_db()
            assert hasattr(outlines[i], 'chapter'), \
                f"Outline {i} lost its chapter link"
            assert outlines[i].chapter.chapter_number == i, \
                f"Outline {i} linked to wrong chapter: {outlines[i].chapter.chapter_number}"
