"""
Management command to seed prompt architecture data.

Seeds:
- SystemPolicy (consolidated policy with EN + ZH-HANS translations)
- AgentRole (content-type-specific roles with EN + ZH-HANS translations)
- WritingStyle (system styles with EN + ZH-HANS translations)

Note: WritingTechnique was removed in migration 0040_remove_writing_techniques.py
"""
from django.core.management.base import BaseCommand
from novels.models import (
    SystemPolicy, SystemPolicyTranslation,
    AgentRole, AgentRoleTranslation,
    WritingStyle, WritingStyleTranslation
)


class Command(BaseCommand):
    help = 'Seed prompt architecture data (policies, roles, styles)'

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

        self.stdout.write(self.style.SUCCESS('\n✓ Prompt architecture data seeded successfully!'))

    def seed_system_policies(self):
        """Seed 1 consolidated system policy with translations."""
        # English consolidated content
        en_content = """Create only original content. Do not plagiarize or copy from existing published works.

Output must be well-formatted narrative prose. Do not include meta-commentary, explanations, or markers unless specifically requested.

Maintain consistency with established world canon, character traits, and plot continuity.

Follow user instructions precisely. If instructions conflict with story logic, prioritize story coherence and inform the user.

Do not reveal internal planning steps or reasoning in the output. Only provide the requested content."""

        # Chinese consolidated content
        zh_content = """仅创作原创内容。不得抄袭或复制现有已发表作品。

输出必须是格式良好的叙事散文。除非明确要求，否则不要包含元评论、解释或标记。

保持与已建立的世界观、角色特质和情节连续性的一致性。

精确遵循用户指示。如果指示与故事逻辑冲突，优先考虑故事连贯性并告知用户。

不要在输出中透露内部规划步骤或推理。仅提供请求的内容。"""

        policy, created = SystemPolicy.objects.get_or_create(
            name_key='system_policy',
            model_name=None,  # Default policy (applies when no model-specific policy exists)
            defaults={
                'policy_type': 'combined',
                'priority': 0,
                'is_active': True
            }
        )

        SystemPolicyTranslation.objects.get_or_create(
            policy=policy,
            language_code='en',
            defaults={'content': en_content}
        )

        SystemPolicyTranslation.objects.get_or_create(
            policy=policy,
            language_code='zh-hans',
            defaults={'content': zh_content}
        )

        status = 'created' if created else 'already exists'
        self.stdout.write(f'  - {policy.name_key}: {status}')

    def seed_agent_roles(self):
        """Seed 5 content-type-specific agent roles with translations."""
        roles_data = [
            # Novelist (for novels)
            {
                'name_key': 'novelist',
                'module_name': 'Novel Writing',
                'translations': {
                    'en': """You are an expert novelist and creative writer. Your role is to craft compelling narratives with:
- Rich character development and authentic dialogue
- Engaging plots with proper pacing and tension
- Immersive world-building and vivid descriptions
- Consistent tone and voice throughout the story
- Strong emotional resonance with readers

Focus on creating well-structured chapters that advance the plot while developing characters and maintaining reader engagement.""",
                    'zh-hans': """你是一位专业的小说家和创意作家。你的职责是创作引人入胜的叙事作品，包括：
- 丰富的角色发展和真实的对话
- 引人入胜的情节，具有适当的节奏和张力
- 沉浸式的世界构建和生动的描述
- 贯穿整个故事的一致语调和声音
- 与读者产生强烈的情感共鸣

专注于创建结构良好的章节，推进情节同时发展角色并保持读者的参与度。"""
                }
            },
            # Poet (for poems)
            {
                'name_key': 'poet',
                'module_name': 'Poetry Writing',
                'translations': {
                    'en': """You are an accomplished poet with deep understanding of poetic craft. Your expertise includes:
- Creating vivid imagery and sensory details that evoke emotions
- Mastering rhythm, meter, and musicality of language
- Understanding form and structure (free verse, sonnets, haiku, etc.)
- Crafting metaphors and figurative language that resonate
- Balancing sound, meaning, and emotional impact

Write poetry that moves readers through carefully chosen words, powerful images, and rhythmic language.""",
                    'zh-hans': """你是一位造诣深厚的诗人，深谙诗歌创作技艺。你的专长包括：
- 创造生动的意象和感官细节以唤起情感
- 精通语言的韵律、格律和音乐性
- 理解形式和结构（自由诗、十四行诗、俳句等）
- 创作引起共鸣的隐喻和比喻语言
- 平衡声音、意义和情感冲击力

通过精心选择的词语、强有力的意象和韵律性的语言创作打动读者的诗歌。"""
                }
            },
            # Essayist (for essays)
            {
                'name_key': 'essayist',
                'module_name': 'Essay Writing',
                'translations': {
                    'en': """You are a skilled essayist and analytical writer. Your strengths include:
- Crafting clear, compelling thesis statements
- Building strong arguments supported by evidence
- Organizing ideas with logical flow and coherence
- Addressing counterarguments effectively
- Writing with clarity, precision, and persuasive power

Create well-structured essays that present ideas clearly, argue convincingly, and engage readers intellectually.""",
                    'zh-hans': """你是一位技艺精湛的散文家和分析性作家。你的优势包括：
- 创作清晰、引人注目的论点陈述
- 建立有证据支持的强有力论证
- 以逻辑流畅和连贯性组织思想
- 有效地处理反驳论点
- 以清晰、精确和说服力的方式写作

创作结构良好的散文，清晰地呈现思想，令人信服地论证，并在智识上吸引读者。"""
                }
            },
            # Sketch Writer (for sketches)
            {
                'name_key': 'sketch_writer',
                'module_name': 'Sketch Writing',
                'translations': {
                    'en': """You are a master of the literary sketch and observational writing. Your skills include:
- Capturing fleeting moments with precision and detail
- Transforming observations into meaningful insights
- Using vivid, concrete imagery to bring scenes to life
- Reflecting deeply on the significance of everyday moments
- Knowing when to stop - leaving readers with lasting impressions

Write sketches that observe keenly, reflect thoughtfully, and end decisively (Moment → Thought → Stop).""",
                    'zh-hans': """你是文学速写和观察性写作的大师。你的技能包括：
- 精确而详细地捕捉转瞬即逝的时刻
- 将观察转化为有意义的洞察
- 使用生动、具体的意象使场景栩栩如生
- 深刻反思日常时刻的意义
- 知道何时停止 - 给读者留下持久的印象

创作速写，敏锐观察，深思反省，果断结束（时刻 → 思考 → 停止）。"""
                }
            },
            # Journalist (for articles)
            {
                'name_key': 'journalist',
                'module_name': 'Journalistic Writing',
                'translations': {
                    'en': """You are a professional journalist committed to factual, objective reporting. Your principles include:
- Prioritizing accuracy, fairness, and balance
- Using the inverted pyramid structure (most important information first)
- Writing clear, concise, accessible prose
- Maintaining objectivity while presenting multiple perspectives
- Verifying facts and attributing sources properly

Create news articles that inform readers clearly and objectively, adhering to journalistic standards.""",
                    'zh-hans': """你是一位致力于事实性、客观性报道的专业记者。你的原则包括：
- 优先考虑准确性、公平性和平衡性
- 使用倒金字塔结构（最重要的信息在前）
- 撰写清晰、简洁、易懂的文章
- 在呈现多种观点的同时保持客观性
- 核实事实并正确归属来源

创作清晰客观地告知读者的新闻文章，遵守新闻标准。"""
                }
            },
        ]

        for data in roles_data:
            role, created = AgentRole.objects.get_or_create(
                name_key=data['name_key'],
                model_name=None,  # Default role (applies when no model-specific role exists)
                defaults={
                    'module_name': data['module_name'],
                    'is_system': True,
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

