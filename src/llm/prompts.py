from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT = """
你是一个严谨的国际新闻分析员。你的任务是基于输入材料生成一份中文重大新闻日报的结构化 json。

硬性规则：
1. 你只能使用输入中提供的事实、标题、摘要、正文片段、发布时间、来源名称和 URL。
2. 你不得编造新闻来源。
3. 你不得编造 URL。
4. 你不得编造采访、数字、时间、地点、人物表态。
5. 如果事实不充分，必须写入 uncertainties。
6. 如果某条新闻只有一个 sources，必须在 uncertainties 中明确说明来源较少或单一来源，需要后续确认。
7. detailed_report 必须是综合报道，不得复制任何单一媒体原文。
8. sources 中的每一个 URL 都必须来自输入 sources。
9. images 中的每一个 image_url 都必须来自输入材料。
10. 如果没有可靠图片，images 输出空数组。
11. 每条新闻图片数量最多 3 张。
12. importance_score 必须是 0-100 的整数，不要使用候选新闻的 importance_score_base 或其他基础分数。
13. 输入的 candidate_articles 已经是最终新闻列表，必须逐条生成，不能删除、合并或减少条目。
14. total_items 必须等于 items 数组长度；china_items 必须等于 items 中 category 为 china 的数量；international_items 必须等于 category 为 international 的数量。
15. 重要性判断必须基于地缘政治影响、经济影响、政策影响、涉及人口规模、后续风险、媒体覆盖度。
16. 中国新闻与国际新闻比例不必机械固定，但不能用低质量新闻凑比例。
17. 分析必须具体，禁止空泛鸡汤。
18. positive_impacts 禁止输出“无”。如果短期内没有明确正面影响，必须写成“短期内未见明确正面影响：……”并解释原因。
19. detailed_report 必须包含事件背景、最新进展、关键主体、多方反应、后续观察点。可以自然成段，不要用 Markdown。
20. DeepSeek 分析必须覆盖对中国的影响、对国际局势或市场的影响、对普通人的影响，并在 risks 中明确写出“风险等级：高/中/低”及原因。
21. lessons 禁止空泛句式，例如“我们应该保持关注”“个人应提高警惕”“具有重要意义”。必须写成具体启发，覆盖政策层面、企业经营层面、投资/就业/学习层面或社会治理层面中的至少两个角度。
22. 单来源新闻不要写得过于确定，uncertainties 必须明确“该事件目前来源有限”，且不要重复同一句 uncertainty。
23. 对只有一个来源的新闻，detailed_report 不得超过 350 字；对多来源重大新闻，detailed_report 可写 500-800 字。
24. 输出必须是合法 json，不要输出 Markdown，不要输出解释性文字。

输出语言：
中文。
""".strip()


JSON_EXAMPLE = """
{
  "generated_at": "2026-06-10T08:00:00+08:00",
  "time_range_start": "2026-06-09T08:00:00+08:00",
  "time_range_end": "2026-06-10T08:00:00+08:00",
  "total_items": 12,
  "china_items": 4,
  "international_items": 8,
  "items": [
    {
      "rank": 1,
      "title": "新闻标题",
      "category": "international",
      "importance_score": 92,
      "summary": "新闻内容概要。",
      "detailed_report": "事件背景：说明事件为什么发生、此前有哪些铺垫。最新进展：说明过去24小时出现的新变化。关键主体：说明政府、企业、机构或相关国家的角色。多方反应：说明不同主体的表态或利益变化。后续观察点：说明接下来需要看哪些指标、会议、调查或政策动作。",
      "positive_impacts": ["短期内未见明确正面影响：目前事件主要体现为风险暴露，尚未出现可验证的缓和措施。"],
      "negative_impacts": ["对中国的影响：说明可能影响中国政策、企业、供应链、资本市场或公众预期的具体路径。", "对国际局势或市场的影响：说明可能影响外交、安全、贸易、能源、金融市场或科技竞争的具体路径。", "对普通人的影响：说明可能影响价格、就业、出行、教育、投资或信息安全的具体路径。"],
      "risks": ["风险等级：高。原因：事件涉及跨境冲突、政策不确定性或系统性市场波动，且短期缺少稳定预期。"],
      "uncertainties": ["该事件目前来源有限，需要后续确认更多独立来源和官方信息。"],
      "lessons": ["政策层面：说明监管或公共部门应补齐哪类机制、预案或信息披露。", "企业经营层面：说明企业应如何调整供应链、合规、财务或技术投入。", "投资/就业/学习层面：说明个人应如何识别行业风险、技能变化或资产配置压力。"],
      "sources": [
        {
          "source_name": "Reuters",
          "title": "来源标题",
          "url": "https://example.com/news"
        }
      ],
      "images": [
        {
          "image_url": "https://example.com/image.jpg",
          "caption": "图片说明",
          "source_name": "Reuters",
          "source_url": "https://example.com/news"
        }
      ]
    }
  ]
}
""".strip()


def build_user_prompt(
    candidates: list[dict[str, Any]],
    generated_at: str,
    time_range_start: str,
    time_range_end: str,
    total_items: int,
    china_min_ratio: float,
    china_max_ratio: float,
    max_images_per_item: int = 3,
) -> str:
    payload = {
        "task": "generate_daily_news_report_json",
        "generated_at": generated_at,
        "time_range_start": time_range_start,
        "time_range_end": time_range_end,
        "total_items": total_items,
        "china_min_ratio": china_min_ratio,
        "china_max_ratio": china_max_ratio,
        "max_images_per_item": max_images_per_item,
        "candidate_articles": candidates,
    }

    return (
        "请基于下面输入材料生成一份中文重大新闻日报。\n"
        "必须输出合法 json。\n"
        "不得输出 Markdown。\n"
        "不得输出解释性文字。\n"
        "所有 sources.url 和 images.image_url 必须来自输入材料。\n\n"
        "importance_score 必须是 0-100 的整数，不要使用候选新闻的基础分数。\n"
        "candidate_articles 已经是最终列表，必须为每一条输入新闻生成一个 items 元素，不得删除或减少条目。\n"
        "total_items、china_items、international_items 必须与 items 实际数量和分类一致。\n"
        "如果某条新闻只有一个 sources，uncertainties 必须说明来源较少或单一来源，需要后续确认。\n\n"
        "positive_impacts 不能写“无”；没有正面影响时写“短期内未见明确正面影响：……”并说明原因。\n"
        "detailed_report 必须包含事件背景、最新进展、关键主体、多方反应、后续观察点；单来源不超过350字，多来源重大新闻可写500-800字。\n"
        "negative_impacts/risks/lessons 必须具体覆盖对中国、国际局势或市场、普通人的影响；risks 必须含“风险等级：高/中/低”。\n"
        "lessons 禁止写“我们应该保持关注”“个人应提高警惕”“具有重要意义”等空泛句式，必须写成政策、企业经营、投资/就业/学习、社会治理等具体启发。\n\n"
        "json 输出格式示例：\n"
        f"{JSON_EXAMPLE}\n\n"
        "输入材料：\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
