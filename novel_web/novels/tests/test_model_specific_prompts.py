"""
Test model-specific System Policies and Agent Roles.

This test suite verifies that different OpenAI models can use different
system policies and agent roles, with proper fallback to default when
model-specific versions don't exist.
"""
import pytest
from novels.models import SystemPolicy, SystemPolicyTranslation, AgentRole, AgentRoleTranslation
from novels.prompt_assembly import PromptAssemblyService


@pytest.fixture
def default_system_policy(db):
    """Create a default system policy (model_name=None)."""
    policy = SystemPolicy.objects.create(
        name_key='system_policy',
        policy_type='behavior',
        model_name=None,  # Default policy
        is_active=True,
        priority=0
    )
    SystemPolicyTranslation.objects.create(
        policy=policy,
        language_code='en',
        content='Default system policy for all models.'
    )
    return policy


@pytest.fixture
def gpt5_system_policy(db):
    """Create a gpt-5.2 specific system policy."""
    policy = SystemPolicy.objects.create(
        name_key='system_policy',
        policy_type='behavior',
        model_name='gpt-5.2',  # Model-specific
        is_active=True,
        priority=0
    )
    SystemPolicyTranslation.objects.create(
        policy=policy,
        language_code='en',
        content='GPT-5.2 specific system policy with advanced capabilities.'
    )
    return policy


@pytest.fixture
def default_writer_role(db):
    """Create a default writer agent role (model_name=None)."""
    role = AgentRole.objects.create(
        name_key='writer',
        module_name='content_generation',
        model_name=None,  # Default role
        is_active=True,
        is_system=True
    )
    AgentRoleTranslation.objects.create(
        role=role,
        language_code='en',
        system_prompt='You are a creative writer. Default instructions for all models.'
    )
    return role


@pytest.fixture
def gpt5_writer_role(db):
    """Create a gpt-5.2 specific writer agent role."""
    role = AgentRole.objects.create(
        name_key='writer',
        module_name='content_generation',
        model_name='gpt-5.2',  # Model-specific
        is_active=True,
        is_system=True
    )
    AgentRoleTranslation.objects.create(
        role=role,
        language_code='en',
        system_prompt='You are an advanced GPT-5.2 creative writer with enhanced reasoning capabilities.'
    )
    return role


@pytest.mark.django_db
class TestModelSpecificSystemPolicy:
    """Test model-specific system policy retrieval and fallback."""

    def test_default_policy_used_when_no_model_specified(self, default_system_policy):
        """Test that default policy is used when model_name is None."""
        prompt = PromptAssemblyService.build_system_prompt(
            agent_role_key='writer',
            language_code='en',
            model_name=None
        )
        assert 'Default system policy for all models' in prompt

    def test_model_specific_policy_used_when_exists(
        self, default_system_policy, gpt5_system_policy, default_writer_role
    ):
        """Test that model-specific policy is used when it exists."""
        prompt = PromptAssemblyService.build_system_prompt(
            agent_role_key='writer',
            language_code='en',
            model_name='gpt-5.2'
        )
        assert 'GPT-5.2 specific system policy' in prompt
        assert 'Default system policy' not in prompt

    def test_fallback_to_default_policy_when_model_specific_missing(
        self, default_system_policy, default_writer_role
    ):
        """Test fallback to default policy when model-specific doesn't exist."""
        # Request gpt-4o-mini but only default exists
        prompt = PromptAssemblyService.build_system_prompt(
            agent_role_key='writer',
            language_code='en',
            model_name='gpt-4o-mini'
        )
        assert 'Default system policy for all models' in prompt

    def test_inactive_model_specific_policy_not_used(
        self, default_system_policy, gpt5_system_policy, default_writer_role
    ):
        """Test that inactive model-specific policies are skipped."""
        # Deactivate the gpt-5.2 specific policy
        gpt5_system_policy.is_active = False
        gpt5_system_policy.save()

        prompt = PromptAssemblyService.build_system_prompt(
            agent_role_key='writer',
            language_code='en',
            model_name='gpt-5.2'
        )
        # Should fall back to default
        assert 'Default system policy for all models' in prompt
        assert 'GPT-5.2 specific' not in prompt


@pytest.mark.django_db
class TestModelSpecificAgentRole:
    """Test model-specific agent role retrieval and fallback."""

    def test_default_role_used_when_no_model_specified(
        self, default_system_policy, default_writer_role
    ):
        """Test that default role is used when model_name is None."""
        prompt = PromptAssemblyService.build_system_prompt(
            agent_role_key='writer',
            language_code='en',
            model_name=None
        )
        assert 'Default instructions for all models' in prompt

    def test_model_specific_role_used_when_exists(
        self, default_system_policy, default_writer_role, gpt5_writer_role
    ):
        """Test that model-specific role is used when it exists."""
        prompt = PromptAssemblyService.build_system_prompt(
            agent_role_key='writer',
            language_code='en',
            model_name='gpt-5.2'
        )
        assert 'advanced GPT-5.2 creative writer' in prompt
        assert 'Default instructions for all models' not in prompt

    def test_fallback_to_default_role_when_model_specific_missing(
        self, default_system_policy, default_writer_role
    ):
        """Test fallback to default role when model-specific doesn't exist."""
        prompt = PromptAssemblyService.build_system_prompt(
            agent_role_key='writer',
            language_code='en',
            model_name='gpt-4o-mini'
        )
        assert 'Default instructions for all models' in prompt

    def test_inactive_model_specific_role_not_used(
        self, default_system_policy, default_writer_role, gpt5_writer_role
    ):
        """Test that inactive model-specific roles are skipped."""
        gpt5_writer_role.is_active = False
        gpt5_writer_role.save()

        prompt = PromptAssemblyService.build_system_prompt(
            agent_role_key='writer',
            language_code='en',
            model_name='gpt-5.2'
        )
        # Should fall back to default
        assert 'Default instructions for all models' in prompt
        assert 'advanced GPT-5.2' not in prompt


@pytest.mark.django_db
class TestModelSpecificCombinations:
    """Test combinations of model-specific policies and roles."""

    def test_both_model_specific_policy_and_role(
        self, default_system_policy, gpt5_system_policy,
        default_writer_role, gpt5_writer_role
    ):
        """Test using both model-specific policy and role."""
        prompt = PromptAssemblyService.build_system_prompt(
            agent_role_key='writer',
            language_code='en',
            model_name='gpt-5.2'
        )
        assert 'GPT-5.2 specific system policy' in prompt
        assert 'advanced GPT-5.2 creative writer' in prompt
        assert 'Default' not in prompt

    def test_model_specific_policy_with_default_role(
        self, default_system_policy, gpt5_system_policy, default_writer_role
    ):
        """Test model-specific policy with default role (mixed)."""
        prompt = PromptAssemblyService.build_system_prompt(
            agent_role_key='writer',
            language_code='en',
            model_name='gpt-5.2'
        )
        # gpt-5.2 policy exists, but role falls back to default
        assert 'GPT-5.2 specific system policy' in prompt
        assert 'Default instructions for all models' in prompt

    def test_default_policy_with_model_specific_role(
        self, default_system_policy, default_writer_role, gpt5_writer_role
    ):
        """Test default policy with model-specific role (mixed)."""
        prompt = PromptAssemblyService.build_system_prompt(
            agent_role_key='writer',
            language_code='en',
            model_name='gpt-5.2'
        )
        # Policy falls back to default, gpt-5.2 role exists
        assert 'Default system policy for all models' in prompt
        assert 'advanced GPT-5.2 creative writer' in prompt

    def test_multiple_models_with_different_policies(
        self, default_system_policy, gpt5_system_policy, default_writer_role
    ):
        """Test that different models get different policies."""
        # Create gpt-4o-mini specific policy
        gpt4_policy = SystemPolicy.objects.create(
            name_key='system_policy',
            policy_type='behavior',
            model_name='gpt-4o-mini',
            is_active=True,
            priority=0
        )
        SystemPolicyTranslation.objects.create(
            policy=gpt4_policy,
            language_code='en',
            content='GPT-4o-mini specific policy for efficiency.'
        )

        # Test gpt-5.2
        prompt_gpt5 = PromptAssemblyService.build_system_prompt(
            agent_role_key='writer',
            language_code='en',
            model_name='gpt-5.2'
        )
        assert 'GPT-5.2 specific' in prompt_gpt5

        # Test gpt-4o-mini
        prompt_gpt4 = PromptAssemblyService.build_system_prompt(
            agent_role_key='writer',
            language_code='en',
            model_name='gpt-4o-mini'
        )
        assert 'GPT-4o-mini specific policy' in prompt_gpt4

        # Test unknown model falls back to default
        prompt_unknown = PromptAssemblyService.build_system_prompt(
            agent_role_key='writer',
            language_code='en',
            model_name='gpt-future-model'
        )
        assert 'Default system policy' in prompt_unknown


@pytest.mark.django_db
class TestAssembleFullPromptWithModel:
    """Test that assemble_full_prompt properly propagates model_name."""

    def test_assemble_full_prompt_with_model_name(
        self, default_system_policy, gpt5_system_policy,
        default_writer_role, gpt5_writer_role
    ):
        """Test that assemble_full_prompt uses model_name parameter."""
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='writer',
            user_prompt='Write a story about a robot.',
            project=None,
            language_code='en',
            context_type='text',
            include_context=False,
            model_name='gpt-5.2'
        )

        # Check that messages were assembled
        assert len(messages) > 0

        # Find the system/developer messages containing our prompts
        all_content = ' '.join([msg['content'] for msg in messages])

        # Should use gpt-5.2 specific versions
        assert 'GPT-5.2 specific system policy' in all_content
        assert 'advanced GPT-5.2 creative writer' in all_content

    def test_assemble_full_prompt_without_model_name(
        self, default_system_policy, gpt5_system_policy,
        default_writer_role, gpt5_writer_role
    ):
        """Test that assemble_full_prompt works without model_name (backward compatible)."""
        messages = PromptAssemblyService.assemble_full_prompt(
            agent_role_key='writer',
            user_prompt='Write a story about a robot.',
            project=None,
            language_code='en',
            context_type='text',
            include_context=False
            # model_name not provided - should use defaults
        )

        all_content = ' '.join([msg['content'] for msg in messages])

        # Should use default versions
        assert 'Default system policy for all models' in all_content
        assert 'Default instructions for all models' in all_content


@pytest.mark.django_db
class TestUniqueConstraints:
    """Test that unique_together constraints work correctly."""

    def test_can_create_multiple_policies_for_different_models(self, db):
        """Test that we can have same name_key with different model_name."""
        # Create default
        policy1 = SystemPolicy.objects.create(
            name_key='system_policy',
            policy_type='behavior',
            model_name=None,
            is_active=True
        )

        # Create gpt-4o-mini specific
        policy2 = SystemPolicy.objects.create(
            name_key='system_policy',
            policy_type='behavior',
            model_name='gpt-4o-mini',
            is_active=True
        )

        # Create gpt-5.2 specific
        policy3 = SystemPolicy.objects.create(
            name_key='system_policy',
            policy_type='behavior',
            model_name='gpt-5.2',
            is_active=True
        )

        # All should exist
        assert SystemPolicy.objects.filter(name_key='system_policy').count() == 3

    def test_cannot_create_duplicate_policy_for_same_model(self, db):
        """Test that duplicate (name_key, model_name) raises error."""
        from django.db import IntegrityError

        SystemPolicy.objects.create(
            name_key='system_policy',
            policy_type='behavior',
            model_name='gpt-5.2',
            is_active=True
        )

        # Try to create duplicate
        with pytest.raises(IntegrityError):
            SystemPolicy.objects.create(
                name_key='system_policy',
                policy_type='behavior',
                model_name='gpt-5.2',  # Same combination
                is_active=True
            )

    def test_can_create_multiple_roles_for_different_models(self, db):
        """Test that we can have same name_key with different model_name."""
        role1 = AgentRole.objects.create(
            name_key='writer',
            module_name='content',
            model_name=None,
            is_active=True
        )

        role2 = AgentRole.objects.create(
            name_key='writer',
            module_name='content',
            model_name='gpt-5.2',
            is_active=True
        )

        assert AgentRole.objects.filter(name_key='writer').count() == 2
