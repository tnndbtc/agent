"""
Management command to seed prompt architecture data.

Seeds:
- SystemPolicy (5 policies with EN + ZH-HANS translations)
- AgentRole (9 roles with EN + ZH-HANS translations)
- WritingStyle (8 system styles with EN + ZH-HANS translations)
- WritingTechnique (6 system techniques with EN + ZH-HANS translations)
"""
from django.core.management.base import BaseCommand
from novels.models import (
    SystemPolicy, SystemPolicyTranslation,
    AgentRole, AgentRoleTranslation,
    WritingStyle, WritingStyleTranslation,
    WritingTechnique, WritingTechniqueTranslation
)


class Command(BaseCommand):
    help = 'Seed prompt architecture data (policies, roles, styles, techniques)'

    def handle(self, *args, **options):
        self.stdout.write('Seeding prompt architecture data...\n')

        # Seed System Policies
        self.stdout.write('Creating System Policies...')
        self.seed_system_policies()

        # Seed Agent Roles
        self.stdout.write('Creating Agent Roles...')
        self.seed_agent_roles()

        # Seed Writing Styles
        self.stdout.write('Creating Writing Styles...')
        self.seed_writing_styles()

        # Seed Writing Techniques
        self.stdout.write('Creating Writing Techniques...')
        self.seed_writing_techniques()

        self.stdout.write(self.style.SUCCESS('\n✓ Prompt architecture data seeded successfully!'))

    def seed_system_policies(self):
        """Seed 5 system policies with translations."""
        policies_data = [
            {
                'name_key': 'copyright_policy',
                'policy_type': 'copyright',
                'priority': 0,
                'translations': {
                    'en': 'Create only original content. Do not plagiarize or copy from existing published works.',
                    'zh-hans': '仅创作原创内容。不得抄袭或复制现有已发表作品。'
                }
            },
            {
                'name_key': 'output_format_policy',
                'policy_type': 'output',
                'priority': 1,
                'translations': {
                    'en': 'Output must be well-formatted narrative prose. Do not include meta-commentary, explanations, or markers unless specifically requested.',
                    'zh-hans': '输出必须是格式良好的叙事散文。除非明确要求，否则不要包含元评论、解释或标记。'
                }
            },
            {
                'name_key': 'coherence_policy',
                'policy_type': 'output',
                'priority': 2,
                'translations': {
                    'en': 'Maintain consistency with established world canon, character traits, and plot continuity.',
                    'zh-hans': '保持与已建立的世界观、角色特质和情节连续性的一致性。'
                }
            },
            {
                'name_key': 'instruction_following_policy',
                'policy_type': 'behavior',
                'priority': 3,
                'translations': {
                    'en': 'Follow user instructions precisely. If instructions conflict with story logic, prioritize story coherence and inform the user.',
                    'zh-hans': '精确遵循用户指示。如果指示与故事逻辑冲突，优先考虑故事连贯性并告知用户。'
                }
            },
            {
                'name_key': 'planning_visibility_policy',
                'policy_type': 'behavior',
                'priority': 4,
                'translations': {
                    'en': 'Do not reveal internal planning steps or reasoning in the output. Only provide the requested content.',
                    'zh-hans': '不要在输出中透露内部规划步骤或推理。仅提供请求的内容。'
                }
            }
        ]

        for data in policies_data:
            policy, created = SystemPolicy.objects.get_or_create(
                name_key=data['name_key'],
                defaults={
                    'policy_type': data['policy_type'],
                    'priority': data['priority'],
                    'is_active': True
                }
            )

            for lang_code, content in data['translations'].items():
                SystemPolicyTranslation.objects.get_or_create(
                    policy=policy,
                    language_code=lang_code,
                    defaults={'content': content}
                )

            status = 'created' if created else 'already exists'
            self.stdout.write(f'  - {policy.name_key}: {status}')

    def seed_agent_roles(self):
        """Seed 9 agent roles with translations."""
        roles_data = [
            {
                'name_key': 'brainstormer',
                'module_name': 'BrainstormingModule',
                'translations': {
                    'en': 'You are a creative writing assistant specializing in generating unique and engaging plot ideas. You excel at combining genres, themes, and creative concepts into compelling story premises.',
                    'zh-hans': '你是一名创意写作助手，专门生成独特且引人入胜的情节创意。你擅长将类型、主题和创意概念结合成引人注目的故事前提。'
                }
            },
            {
                'name_key': 'plotter',
                'module_name': 'PlotGenerator',
                'translations': {
                    'en': 'You are an expert in story structure and three-act narrative design. You create detailed plot outlines with strong character arcs, clear conflicts, and satisfying resolutions.',
                    'zh-hans': '你是故事结构和三幕叙事设计专家。你创建详细的情节大纲，包含强大的角色弧线、清晰的冲突和令人满意的解决方案。'
                }
            },
            {
                'name_key': 'character_creator',
                'module_name': 'CharacterGenerator',
                'translations': {
                    'en': 'You are a character development specialist. You create complex, multi-dimensional characters with compelling motivations, flaws, and character arcs.',
                    'zh-hans': '你是角色发展专家。你创建复杂、多维度的角色，具有引人注目的动机、缺陷和角色弧线。'
                }
            },
            {
                'name_key': 'writer',
                'module_name': 'ChapterWriter',
                'translations': {
                    'en': 'You are a professional novelist writing engaging narrative prose. You create vivid scenes, natural dialogue, and emotionally resonant storytelling.',
                    'zh-hans': '你是一位专业小说家，撰写引人入胜的叙事散文。你创作生动的场景、自然的对话和情感共鸣的故事叙述。'
                }
            },
            {
                'name_key': 'text_modifier',
                'module_name': 'AIModificationService',
                'translations': {
                    'en': 'You are a text editing assistant that helps improve and modify narrative content based on user instructions. You maintain the original voice and style while applying the requested changes.',
                    'zh-hans': '你是文本编辑助手，根据用户指示帮助改进和修改叙事内容。你在应用请求的更改时保持原始声音和风格。'
                }
            },
            {
                'name_key': 'setting_creator',
                'module_name': 'SettingGenerator',
                'translations': {
                    'en': 'You are a world-building specialist who creates rich, immersive settings and locations. You excel at designing atmospheric environments that enhance the story and provide depth to the narrative world.',
                    'zh-hans': '你是世界观构建专家，创建丰富、沉浸式的设定和地点。你擅长设计具有氛围感的环境，增强故事并为叙事世界提供深度。'
                }
            },
            {
                'name_key': 'editor',
                'module_name': 'EditorModule',
                'translations': {
                    'en': 'You are a professional editor specializing in narrative fiction. You improve writing quality, fix grammar and style issues, enhance dialogue, and ensure consistency while preserving the author\'s voice.',
                    'zh-hans': '你是专业的叙事小说编辑。你提高写作质量，修正语法和风格问题，增强对话，确保一致性，同时保留作者的声音。'
                }
            },
            {
                'name_key': 'consistency_checker',
                'module_name': 'ConsistencyChecker',
                'translations': {
                    'en': 'You are a continuity and consistency analyst for narrative fiction. You identify inconsistencies in character traits, plot details, world-building elements, and timeline events to maintain story coherence.',
                    'zh-hans': '你是叙事小说的连续性和一致性分析师。你识别角色特征、情节细节、世界观元素和时间线事件中的不一致，以保持故事连贯性。'
                }
            }
        ]

        for data in roles_data:
            role, created = AgentRole.objects.get_or_create(
                name_key=data['name_key'],
                defaults={
                    'module_name': data['module_name'],
                    'is_active': True
                }
            )

            for lang_code, system_prompt in data['translations'].items():
                AgentRoleTranslation.objects.get_or_create(
                    role=role,
                    language_code=lang_code,
                    defaults={'system_prompt': system_prompt}
                )

            status = 'created' if created else 'already exists'
            self.stdout.write(f'  - {role.name_key}: {status}')

    def seed_writing_styles(self):
        """Seed 8 system writing styles with translations."""
        styles_data = [
            {
                'name_key': 'xuanhuan',
                'pacing': 'fast',
                'tone': 'action-oriented',
                'paragraph_length': 'short',
                'dialogue_ratio': 'high',
                'cliffhanger_enabled': True,
                'translations': {
                    'en': {
                        'name': 'Xuanhuan (玄幻)',
                        'description': 'Chinese fantasy style with fast-paced action, power progression, and cultivation elements',
                        'instructions': 'Use short, punchy paragraphs (2-4 sentences). High dialogue ratio. Include power levels, cultivation stages, and face/honor dynamics. Every chapter must contain: (1) one power advancement or setback, (2) one emotional beat, (3) a cliffhanger hook at the end. Emphasize 爽点 (payoff moments) where protagonist demonstrates growth.'
                    },
                    'zh-hans': {
                        'name': '玄幻',
                        'description': '快节奏动作、力量进阶和修炼元素的中国奇幻风格',
                        'instructions': '使用简短有力的段落（2-4句）。高对话比例。包含实力等级、修炼境界和面子/荣誉动态。每章必须包含：(1)一次力量提升或挫折，(2)一个情感节拍，(3)章节结尾的悬念。强调爽点（主角展示成长的回报时刻）。'
                    }
                }
            },
            {
                'name_key': 'wuxia',
                'pacing': 'medium',
                'tone': 'honor-driven',
                'paragraph_length': 'medium',
                'dialogue_ratio': 'medium',
                'cliffhanger_enabled': False,
                'translations': {
                    'en': {
                        'name': 'Wuxia (武侠)',
                        'description': 'Martial arts fiction emphasizing honor, loyalty, and martial prowess',
                        'instructions': 'Balance action with character introspection. Emphasize martial arts techniques with poetic descriptions. Focus on themes of justice (江湖), honor, revenge, and loyalty. Include martial arts sects, masters, and disciples. Use traditional Chinese values and philosophical depth.'
                    },
                    'zh-hans': {
                        'name': '武侠',
                        'description': '强调荣誉、忠诚和武艺的武侠小说',
                        'instructions': '平衡动作与角色内省。用诗意描述强调武术技巧。关注江湖、荣誉、复仇和忠诚主题。包含武术门派、师傅和弟子。使用传统中国价值观和哲学深度。'
                    }
                }
            },
            {
                'name_key': 'literary_fiction',
                'pacing': 'slow',
                'tone': 'introspective',
                'paragraph_length': 'long',
                'dialogue_ratio': 'low',
                'cliffhanger_enabled': False,
                'translations': {
                    'en': {
                        'name': 'Literary Fiction',
                        'description': 'Character-driven, introspective narrative with rich prose',
                        'instructions': 'Focus on internal character development and psychological depth. Use rich, descriptive prose with metaphors and symbolism. Emphasize themes and subtext over plot. Slower pacing allows for reflection and atmosphere. Explore complex emotions and moral ambiguity.'
                    },
                    'zh-hans': {
                        'name': '文学小说',
                        'description': '角色驱动、内省叙事，具有丰富的散文',
                        'instructions': '关注角色内在发展和心理深度。使用丰富的描述性散文，包含隐喻和象征。强调主题和潜台词胜过情节。较慢的节奏允许反思和氛围营造。探索复杂情感和道德模糊性。'
                    }
                }
            },
            {
                'name_key': 'thriller',
                'pacing': 'fast',
                'tone': 'suspenseful',
                'paragraph_length': 'short',
                'dialogue_ratio': 'medium',
                'cliffhanger_enabled': True,
                'translations': {
                    'en': {
                        'name': 'Thriller',
                        'description': 'Fast-paced suspense with tension and twists',
                        'instructions': 'Maintain high tension throughout. Use short paragraphs to increase pace during action. Plant clues and red herrings. Build to climactic reveals. End chapters with twists or cliffhangers. Create sense of urgency and danger.'
                    },
                    'zh-hans': {
                        'name': '惊悚',
                        'description': '快节奏悬疑，充满紧张和转折',
                        'instructions': '始终保持高度紧张。在动作场景使用短段落加快节奏。埋下线索和误导。构建高潮揭示。章节以转折或悬念结束。营造紧迫感和危险感。'
                    }
                }
            },
            {
                'name_key': 'romance',
                'pacing': 'medium',
                'tone': 'emotional',
                'paragraph_length': 'medium',
                'dialogue_ratio': 'high',
                'cliffhanger_enabled': False,
                'translations': {
                    'en': {
                        'name': 'Romance',
                        'description': 'Emotionally-driven narrative focusing on relationships',
                        'instructions': 'Focus on emotional beats and relationship development. Use dialogue to reveal character chemistry and connection. Balance external conflict with internal emotional arcs. Show vulnerability and intimacy. Build romantic tension gradually.'
                    },
                    'zh-hans': {
                        'name': '言情',
                        'description': '情感驱动的叙事，专注于关系',
                        'instructions': '关注情感节拍和关系发展。使用对话展现角色化学反应和联系。平衡外部冲突与内部情感弧线。展示脆弱性和亲密感。逐步构建浪漫张力。'
                    }
                }
            },
            {
                'name_key': 'scifi',
                'pacing': 'medium',
                'tone': 'speculative',
                'paragraph_length': 'medium',
                'dialogue_ratio': 'medium',
                'cliffhanger_enabled': True,
                'translations': {
                    'en': {
                        'name': 'Science Fiction',
                        'description': 'Speculative fiction exploring technology, future, and scientific concepts',
                        'instructions': 'Ground speculative elements in logical world-building. Use technical details sparingly but accurately. Focus on how technology affects characters and society. Balance hard sci-fi concepts with human stories. Explore philosophical implications of technological advances.'
                    },
                    'zh-hans': {
                        'name': '科幻',
                        'description': '探索技术、未来和科学概念的推测性小说',
                        'instructions': '将推测性元素建立在逻辑世界观上。技术细节使用适度但准确。关注技术如何影响角色和社会。平衡硬科幻概念与人性故事。探索技术进步的哲学意义。'
                    }
                }
            },
            {
                'name_key': 'fantasy',
                'pacing': 'medium',
                'tone': 'epic',
                'paragraph_length': 'medium',
                'dialogue_ratio': 'medium',
                'cliffhanger_enabled': True,
                'translations': {
                    'en': {
                        'name': 'Fantasy',
                        'description': 'Epic fantasy with world-building, magic systems, and quests',
                        'instructions': 'Build rich, immersive world with clear magic system rules. Use descriptive prose for settings and magic. Focus on hero journey and epic stakes. Balance action with world-building. Create sense of wonder and adventure.'
                    },
                    'zh-hans': {
                        'name': '奇幻',
                        'description': '具有世界观、魔法系统和任务的史诗奇幻',
                        'instructions': '构建丰富、沉浸式的世界，具有清晰的魔法系统规则。使用描述性散文描绘设定和魔法。关注英雄之旅和史诗赌注。平衡动作与世界观构建。营造奇迹和冒险感。'
                    }
                }
            },
            {
                'name_key': 'modern_urban',
                'pacing': 'fast',
                'tone': 'contemporary',
                'paragraph_length': 'short',
                'dialogue_ratio': 'high',
                'cliffhanger_enabled': True,
                'translations': {
                    'en': {
                        'name': 'Modern Urban',
                        'description': 'Contemporary urban settings with fast-paced plot',
                        'instructions': 'Use contemporary language and references. Set in modern cities with realistic details. Fast-paced with snappy dialogue. Focus on ambition, success, and modern conflicts. Include technology, social media, and current events naturally.'
                    },
                    'zh-hans': {
                        'name': '都市爽文',
                        'description': '现代都市背景，快节奏情节',
                        'instructions': '使用现代语言和参考。设定在现代城市，具有真实细节。快节奏，对话简洁有力。关注野心、成功和现代冲突。自然地包含技术、社交媒体和当前事件。'
                    }
                }
            },
            # Content-type-specific styles
            {
                'name_key': 'poem',
                'content_type': 'poem',
                'pacing': 'slow',
                'tone': 'lyrical',
                'paragraph_length': 'short',
                'dialogue_ratio': 'low',
                'cliffhanger_enabled': False,
                'translations': {
                    'en': {
                        'name': 'Poem Style',
                        'description': 'Lyrical and imagery-focused style for poetry creation',
                        'instructions': '''Focus on creating vivid imagery and sensory details that evoke emotion.

Key elements:
- Use concrete, specific images that appeal to the senses
- Pay attention to rhythm and musicality of language
- Employ metaphor, simile, and figurative language
- Consider line breaks and stanza structure for emphasis
- Create emotional resonance through word choice
- Use sound devices like alliteration, assonance, consonance when appropriate
- Build layers of meaning through imagery and symbolism
- Keep language precise and economical - every word should earn its place'''
                    },
                    'zh-hans': {
                        'name': '诗歌风格',
                        'description': '抒情性和意象为主的诗歌创作风格',
                        'instructions': '''专注于创造生动的意象和感官细节以唤起情感。

关键要素：
- 使用具体的、特定的意象来吸引感官
- 注意语言的节奏和音乐性
- 运用隐喻、明喻和比喻性语言
- 考虑断行和节结构以强调重点
- 通过词语选择创造情感共鸣
- 适当使用头韵、元音和辅音韵等声音手法
- 通过意象和象征建立多层含义
- 保持语言精确和简洁——每个词都应该发挥作用'''
                    }
                }
            },
            {
                'name_key': 'essay',
                'content_type': 'essay',
                'pacing': 'medium',
                'tone': 'analytical',
                'paragraph_length': 'medium',
                'dialogue_ratio': 'low',
                'cliffhanger_enabled': False,
                'translations': {
                    'en': {
                        'name': 'Essay Style',
                        'description': 'Analytical and structured style for essay writing',
                        'instructions': '''Develop a clear thesis and support it with logical argumentation and evidence.

Key elements:
- Begin with a strong thesis statement that makes a clear argument
- Organize ideas with topic sentences that support the thesis
- Use evidence, examples, and analysis to build your argument
- Address potential counterarguments to strengthen your position
- Maintain formal, academic tone while remaining engaging
- Use transitions to guide readers through your logic
- Build paragraphs around single, well-developed ideas
- Conclude by reinforcing your thesis and its implications
- Cite sources appropriately when using external evidence'''
                    },
                    'zh-hans': {
                        'name': '论文风格',
                        'description': '分析性和结构化的论文写作风格',
                        'instructions': '''发展一个清晰的论点，并用逻辑论证和证据来支持它。

关键要素：
- 以强有力的论点陈述开始，提出明确的论点
- 用支持论点的主题句组织想法
- 使用证据、例子和分析来构建你的论证
- 处理潜在的反驳论点以加强你的立场
- 保持正式的学术语气，同时保持吸引力
- 使用过渡词引导读者理解你的逻辑
- 围绕单一的、充分发展的想法构建段落
- 通过强化你的论点及其含义来总结
- 在使用外部证据时适当引用来源'''
                    }
                }
            },
            {
                'name_key': 'sketch',
                'content_type': 'sketch',
                'pacing': 'medium',
                'tone': 'descriptive',
                'paragraph_length': 'medium',
                'dialogue_ratio': 'medium',
                'cliffhanger_enabled': False,
                'translations': {
                    'en': {
                        'name': 'Sketch Style',
                        'description': 'Observational and descriptive style for literary sketches',
                        'instructions': '''Capture a moment, scene, or character with keen observation and vivid detail.

Key elements:
- Observe with precision - notice specific, concrete details
- Use sensory details to bring the scene to life (sight, sound, smell, texture)
- Capture the atmosphere and mood of the moment
- Include brief character observations or interactions that reveal personality
- Balance description with subtle reflection or insight
- Maintain a present, immediate quality - show what you're witnessing
- Keep the scope focused on a single moment or scene
- Let details speak for themselves without over-explaining
- End with a resonant image or observation that lingers'''
                    },
                    'zh-hans': {
                        'name': '速写风格',
                        'description': '观察性和描述性的文学速写风格',
                        'instructions': '''用敏锐的观察和生动的细节捕捉一个时刻、场景或人物。

关键要素：
- 精确观察——注意具体的、具体的细节
- 使用感官细节使场景生动起来（视觉、声音、气味、质感）
- 捕捉时刻的氛围和情绪
- 包括简短的人物观察或互动，揭示个性
- 平衡描述与微妙的反思或洞察
- 保持当下的、即时的品质——展示你正在目睹的内容
- 将范围集中在单一时刻或场景上
- 让细节自己说话，不要过度解释
- 以一个引人共鸣的意象或观察结束'''
                    }
                }
            },
            {
                'name_key': 'article',
                'content_type': 'article',
                'pacing': 'fast',
                'tone': 'neutral',
                'paragraph_length': 'short',
                'dialogue_ratio': 'medium',
                'cliffhanger_enabled': False,
                'translations': {
                    'en': {
                        'name': 'Article Style',
                        'description': 'Journalistic style for news and feature articles',
                        'instructions': '''Write clear, factual, and engaging journalism that informs readers efficiently.

Key elements:
- Lead with the most important information (inverted pyramid structure)
- Use short, punchy paragraphs (typically 2-3 sentences)
- Write clear, concise sentences in active voice
- Present facts objectively without editorial bias
- Include relevant quotes from credible sources
- Provide context and background where necessary
- Use specific details and concrete examples
- Attribute all claims and information to sources
- Maintain professional, accessible tone
- End with additional context or forward-looking perspective
- Follow AP style guidelines for formatting'''
                    },
                    'zh-hans': {
                        'name': '文章风格',
                        'description': '新闻和专题文章的新闻风格',
                        'instructions': '''撰写清晰、真实和引人入胜的新闻报道，有效地向读者提供信息。

关键要素：
- 以最重要的信息开头（倒金字塔结构）
- 使用简短有力的段落（通常2-3句）
- 用主动语态写清晰简洁的句子
- 客观地呈现事实，不带编辑偏见
- 包括来自可信来源的相关引述
- 在必要时提供背景和背景信息
- 使用具体细节和具体例子
- 将所有声明和信息归因于来源
- 保持专业、易于理解的语气
- 以额外的背景或前瞻性的视角结束
- 遵循AP风格指南进行格式化'''
                    }
                }
            }
        ]

        for data in styles_data:
            style, created = WritingStyle.objects.get_or_create(
                name_key=data['name_key'],
                created_by=None,  # System style
                defaults={
                    'is_system': True,
                    'public': True,
                    'content_type': data.get('content_type', 'novel'),  # Default to novel
                    'pacing': data['pacing'],
                    'tone': data['tone'],
                    'paragraph_length': data['paragraph_length'],
                    'dialogue_ratio': data['dialogue_ratio'],
                    'cliffhanger_enabled': data['cliffhanger_enabled']
                }
            )

            for lang_code, trans_data in data['translations'].items():
                WritingStyleTranslation.objects.get_or_create(
                    style=style,
                    language_code=lang_code,
                    defaults={
                        'name': trans_data['name'],
                        'description': trans_data['description'],
                        'instructions': trans_data['instructions']
                    }
                )

            status = 'created' if created else 'already exists'
            self.stdout.write(f'  - {style.name_key}: {status}')

    def seed_writing_techniques(self):
        """Seed 6 system writing techniques with translations."""
        techniques_data = [
            {
                'name_key': 'show_dont_tell',
                'category': 'narrative',
                'translations': {
                    'en': {
                        'name': "Show, Don't Tell",
                        'description': 'Demonstrate through action and sensory details',
                        'instructions': 'Demonstrate character emotions and plot developments through actions, dialogue, and sensory details rather than direct exposition. Use body language, facial expressions, and environmental cues to convey information.'
                    },
                    'zh-hans': {
                        'name': '展示而非叙述',
                        'description': '通过动作和感官细节展示',
                        'instructions': '通过动作、对话和感官细节展示角色情感和情节发展，而非直接阐述。使用肢体语言、面部表情和环境线索传达信息。'
                    }
                }
            },
            {
                'name_key': 'foreshadowing',
                'category': 'pacing',
                'translations': {
                    'en': {
                        'name': 'Foreshadowing',
                        'description': 'Plant hints about future events',
                        'instructions': 'Plant subtle hints and clues about future events to build anticipation. Use symbolism, dialogue, and seemingly minor details that gain significance later. Create payoffs for careful readers.'
                    },
                    'zh-hans': {
                        'name': '伏笔',
                        'description': '埋下关于未来事件的暗示',
                        'instructions': '埋下关于未来事件的微妙暗示和线索，营造期待感。使用象征、对话和看似次要但后来变得重要的细节。为细心的读者创造回报。'
                    }
                }
            },
            {
                'name_key': 'dialogue_subtext',
                'category': 'dialogue',
                'translations': {
                    'en': {
                        'name': 'Dialogue Subtext',
                        'description': 'Characters say one thing, mean another',
                        'instructions': 'Characters should not always say exactly what they mean. Use subtext, hidden agendas, and unspoken tensions. What characters don\'t say is often as important as what they do say. Create layers of meaning in conversations.'
                    },
                    'zh-hans': {
                        'name': '对话潜台词',
                        'description': '角色言不由衷',
                        'instructions': '角色不应总是直接表达真实意图。使用潜台词、隐藏议程和未言明的紧张关系。角色未说的内容往往与已说的同样重要。在对话中创建多层含义。'
                    }
                }
            },
            {
                'name_key': 'sensory_immersion',
                'category': 'description',
                'translations': {
                    'en': {
                        'name': 'Sensory Immersion',
                        'description': 'Engage all five senses',
                        'instructions': 'Engage all five senses (sight, sound, smell, taste, touch) to create immersive scenes. Don\'t rely only on visual descriptions. Use sensory details to anchor readers in the scene and evoke emotional responses.'
                    },
                    'zh-hans': {
                        'name': '感官沉浸',
                        'description': '调动五感',
                        'instructions': '调动五感（视觉、听觉、嗅觉、味觉、触觉）创建沉浸式场景。不要仅依赖视觉描述。使用感官细节将读者锚定在场景中并唤起情感反应。'
                    }
                }
            },
            {
                'name_key': 'varied_sentence_rhythm',
                'category': 'narrative',
                'translations': {
                    'en': {
                        'name': 'Varied Sentence Rhythm',
                        'description': 'Mix short and long sentences for flow',
                        'instructions': 'Vary sentence length and structure to control pacing. Short sentences for tension and action. Longer sentences for description and reflection. Avoid monotonous rhythm. Use sentence structure to create music in prose.'
                    },
                    'zh-hans': {
                        'name': '句式节奏变化',
                        'description': '混合长短句保持流畅',
                        'instructions': '变化句子长度和结构来控制节奏。短句用于紧张和动作。长句用于描述和反思。避免单调节奏。使用句子结构在散文中创造音乐性。'
                    }
                }
            },
            {
                'name_key': 'character_voice_consistency',
                'category': 'character',
                'translations': {
                    'en': {
                        'name': 'Character Voice Consistency',
                        'description': 'Maintain distinct character speech patterns',
                        'instructions': 'Each character should have a distinct voice in dialogue and internal thoughts. Consider their background, education, personality, and emotional state. Keep their speech patterns consistent throughout the story (性格不崩). Voice changes should reflect character development.'
                    },
                    'zh-hans': {
                        'name': '角色语言一致性',
                        'description': '保持独特的角色语言模式',
                        'instructions': '每个角色在对话和内心思想中应有独特的声音。考虑他们的背景、教育、性格和情绪状态。在整个故事中保持语言模式一致（性格不崩）。声音变化应反映角色发展。'
                    }
                }
            }
        ]

        for data in techniques_data:
            technique, created = WritingTechnique.objects.get_or_create(
                name_key=data['name_key'],
                defaults={
                    'is_system': True,
                    'public': True,
                    'category': data['category'],
                    'created_by': None  # System technique
                }
            )

            for lang_code, trans_data in data['translations'].items():
                WritingTechniqueTranslation.objects.get_or_create(
                    technique=technique,
                    language_code=lang_code,
                    defaults={
                        'name': trans_data['name'],
                        'description': trans_data['description'],
                        'instructions': trans_data['instructions']
                    }
                )

            status = 'created' if created else 'already exists'
            self.stdout.write(f'  - {technique.name_key}: {status}')
