"""
Gemini AI analyzer for WhatsApp chats.
Extracts business intelligence for ChatChaos International from Lebanese market conversations.
"""

import os
import json
import re
from typing import Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv('.env.txt')
_API_KEY: str = os.getenv('GEMINI_API_KEY', '').strip()

MODEL    = 'gemini-2.5-flash'
MAX_CHARS = 40_000
KEEP_HEAD = 0.30
KEEP_TAIL = 0.70

# ── Lebanese area taxonomy ────────────────────────────────────────────────────

AREA_TAXONOMY = [
    # Beirut — East
    'Ashrafieh', 'Gemmayzeh', 'Mar Mikhael', 'Geitawi', 'Rmeil', 'Saifi',
    'Bourj Hammoud', 'Sin el Fil', 'Dora', 'Jdeideh', 'Fanar', 'Dekwaneh',
    'Furn el Chebbak', 'Ain Saadeh',
    # Beirut — West / Central
    'Downtown Beirut', 'Solidere', 'Hamra', 'Verdun', 'Raouche', 'Ain el Mreisseh',
    'Manara', 'Ras Beirut', 'Badaro', 'Mar Elias', 'Bachoura', 'Sanayeh',
    'Zokak el Blat', 'Corniche el Mazraa', 'Ramlet el Bayda',
    # South Beirut / Inner Suburbs
    'Chiyah', 'Ghobeiry', 'Haret Hreik', 'Bir Hassan', 'Jnah', 'Ouzai',
    'Laylaki', 'Kafaat',
    # Baabda / Metn (East suburbs)
    'Hazmieh', 'Baabda', 'Yarze', 'Mansourieh', 'Mtayleb', 'Bikfaya',
    'Beit Meri', 'Broumana', 'Aintoura', 'Metn',
    # Keserwan / North Coast
    'Zalka', 'Dbayeh', 'Naccache', 'Antelias', 'Zouk Mosbeh', 'Zouk Mikael',
    'Jounieh', 'Kaslik', 'Safra', 'Tabarja', 'Kfar Aabida',
    # Jbeil (Byblos area)
    'Jbeil', 'Byblos', 'Amchit', 'Blat',
    # South Lebanon
    'Saida', 'Tyre', 'Nabatieh', 'Bint Jbeil', 'Marjayoun', 'Hasbaya',
    'Jezzine', 'Khiam', 'Kfar Rumman',
    # Greater South / Khalde corridor
    'Khalde', 'Damour', 'Naameh', 'Kfarchima', 'Barja', 'Rmeileh', 'Jiyeh',
    # North Lebanon
    'Tripoli', 'Mina', 'Zgharta', 'Batroun', 'Koura', 'Minieh',
    'Halba', 'Akkar', 'Bcharre', 'Ehden', 'Kousba',
    # Bekaa Valley
    'Zahle', 'Chtaura', 'Baalbek', 'Rayak', 'Anjar', 'Hermel',
    'Yohmor', 'Taalbaya',
    # Chouf / Aley (Mountain)
    'Aley', 'Chouf', 'Barouk', 'Deir el Qamar', 'Beiteddine', 'Jdita',
    'Bchamoun', 'Souk el Gharb',
]

AREA_ALIASES: Dict[str, str] = {
    'achrafieh': 'Ashrafieh', 'achrafiyeh': 'Ashrafieh', 'achrafiyet': 'Ashrafieh',
    'al ashrafieh': 'Ashrafieh', 'gemmayze': 'Gemmayzeh', 'gemmayseh': 'Gemmayzeh',
    'gemmayzeh': 'Gemmayzeh', 'mar mikhael': 'Mar Mikhael', 'mar mikhaël': 'Mar Mikhael',
    'bourj hammoud': 'Bourj Hammoud', 'burj hammoud': 'Bourj Hammoud',
    'sin el fil': 'Sin el Fil', 'sinelfil': 'Sin el Fil',
    'byblos': 'Jbeil', 'jbail': 'Jbeil', 'bybel': 'Jbeil', 'byblus': 'Jbeil',
    'sidon': 'Saida', 'saïda': 'Saida', 'sayda': 'Saida', 'saïde': 'Saida',
    'sour': 'Tyre', 'sur': 'Tyre', 'tyr': 'Tyre', 'es-sour': 'Tyre',
    'tripoli': 'Tripoli', 'trablous': 'Tripoli', 'trablus': 'Tripoli', 'tarabulus': 'Tripoli',
    'zahle': 'Zahle', 'zahleh': 'Zahle', 'zahlé': 'Zahle',
    'metn': 'Metn', 'el metn': 'Metn',
    'jounieh': 'Jounieh', 'jouniye': 'Jounieh', 'juniyah': 'Jounieh',
    'hazmieh': 'Hazmieh', 'hazmiyeh': 'Hazmieh',
    'baabda': 'Baabda', 'baaabda': 'Baabda',
    'raouche': 'Raouche', 'rawche': 'Raouche', 'rawshe': 'Raouche',
    'hamra': 'Hamra', 'el hamra': 'Hamra',
    'verdun': 'Verdun', 'ferdane': 'Verdun',
    'haret hreik': 'Haret Hreik', 'haret el hreik': 'Haret Hreik',
    'ouzai': 'Ouzai', 'ouzaai': 'Ouzai',
    'chiyah': 'Chiyah', 'el chiyah': 'Chiyah', 'ashiya': 'Chiyah',
    'ghobeyri': 'Ghobeiry', 'ghobeiry': 'Ghobeiry',
    'nabatiyeh': 'Nabatieh', 'nabatiye': 'Nabatieh',
    'bchamoun': 'Bchamoun', 'bshamoun': 'Bchamoun',
    'khalde': 'Khalde', 'khalda': 'Khalde',
    'kfarchima': 'Kfarchima', 'kfarshima': 'Kfarchima',
    'barja': 'Barja', 'برجا': 'Barja',
    'rmeileh': 'Rmeileh', 'jiyeh': 'Jiyeh', 'jieh': 'Jiyeh',
    'dbayeh': 'Dbayeh', 'dbayyeh': 'Dbayeh',
    'batroun': 'Batroun', 'batrun': 'Batroun',
    'zgharta': 'Zgharta', 'zghorta': 'Zgharta',
    'akkar': 'Akkar', 'aley': 'Aley', 'alay': 'Aley',
    'baalbek': 'Baalbek', 'balbek': 'Baalbek', 'baalbeck': 'Baalbek',
    'chtaura': 'Chtaura', 'shtora': 'Chtaura',
    'chouf': 'Chouf', 'el chouf': 'Chouf',
    'koura': 'Koura', 'el koura': 'Koura',
    'bcharre': 'Bcharre', 'bsharri': 'Bcharre',
    'marjayoun': 'Marjayoun', 'marjeyoun': 'Marjayoun',
    'jezzine': 'Jezzine', 'jazzine': 'Jezzine',
    'antelias': 'Antelias', 'antelyas': 'Antelias',
    'downtown': 'Downtown Beirut', 'city centre': 'Downtown Beirut',
    'solidere': 'Solidere', 'wust el balad': 'Downtown Beirut',
    'kaslik': 'Kaslik', 'jounieh kaslik': 'Kaslik',
    # Arabic-script
    'الأشرفية': 'Ashrafieh', 'أشرفية': 'Ashrafieh', 'الجميزة': 'Gemmayzeh',
    'مار مخايل': 'Mar Mikhael', 'برج حمود': 'Bourj Hammoud', 'سن الفيل': 'Sin el Fil',
    'الدورة': 'Dora', 'الجديدة': 'Jdeideh', 'الفنار': 'Fanar', 'الدكوانة': 'Dekwaneh',
    'فرن الشباك': 'Furn el Chebbak', 'وسط البيروت': 'Downtown Beirut',
    'وسط بيروت': 'Downtown Beirut', 'الحمراء': 'Hamra', 'الروشة': 'Raouche',
    'عين المريسة': 'Ain el Mreisseh', 'المنارة': 'Manara', 'بدارو': 'Badaro',
    'مار الياس': 'Mar Elias', 'الصنائع': 'Sanayeh', 'رملة البيضاء': 'Ramlet el Bayda',
    'فردان': 'Verdun', 'الشياح': 'Chiyah', 'الغبيري': 'Ghobeiry',
    'حارة حريك': 'Haret Hreik', 'بئر حسن': 'Bir Hassan', 'الأوزاعي': 'Ouzai',
    'الحازمية': 'Hazmieh', 'بعبدا': 'Baabda', 'يرزة': 'Yarze',
    'المنصورية': 'Mansourieh', 'المتيلب': 'Mtayleb', 'بيت مري': 'Beit Meri',
    'برمانا': 'Broumana', 'بيكفيا': 'Bikfaya', 'الزلقا': 'Zalka', 'ضبية': 'Dbayeh',
    'النقاش': 'Naccache', 'أنطلياس': 'Antelias', 'جونيه': 'Jounieh',
    'الكسليك': 'Kaslik', 'طبرجا': 'Tabarja', 'جبيل': 'Jbeil', 'بيبلوس': 'Jbeil',
    'صيدا': 'Saida', 'صور': 'Tyre', 'النبطية': 'Nabatieh', 'بنت جبيل': 'Bint Jbeil',
    'مرجعيون': 'Marjayoun', 'جزين': 'Jezzine', 'الخلدة': 'Khalde', 'خلدة': 'Khalde',
    'الدامور': 'Damour', 'كفرشيما': 'Kfarchima', 'طرابلس': 'Tripoli', 'المينا': 'Mina',
    'زغرتا': 'Zgharta', 'البترون': 'Batroun', 'الكورة': 'Koura', 'عكار': 'Akkar',
    'بشري': 'Bcharre', 'إهدن': 'Ehden', 'زحلة': 'Zahle', 'شتورة': 'Chtaura',
    'بعلبك': 'Baalbek', 'الرياق': 'Rayak', 'عنجر': 'Anjar', 'الهرمل': 'Hermel',
    'عاليه': 'Aley', 'الشوف': 'Chouf', 'الباروك': 'Barouk', 'دير القمر': 'Deir el Qamar',
    'بيت الدين': 'Beiteddine', 'بشامون': 'Bchamoun',
}


def normalise_area(area: Optional[str]) -> Optional[str]:
    if not area:
        return area
    return AREA_ALIASES.get(area.lower(), area)


def _truncate(text: str) -> str:
    if len(text) <= MAX_CHARS:
        return text
    head_end   = int(MAX_CHARS * KEEP_HEAD)
    tail_start = len(text) - int(MAX_CHARS * KEEP_TAIL)
    return (
        text[:head_end]
        + '\n\n... [TRUNCATED — middle portion omitted] ...\n\n'
        + text[tail_start:]
    )


# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert business intelligence assistant for ChatChaos International,
a Lebanese concrete and construction materials company. Your role is to analyze WhatsApp
conversation exports and extract structured commercial intelligence from client, contractor,
and project communications.

LANGUAGE CONTEXT:
- Conversations may be in English, Arabic (MSA or Lebanese/Levantine dialect), French, or
  Arabizi (Arabic written in Latin letters)
- Common Arabizi: "shu" (what), "kifak" (how are you), "3am" (present tense marker),
  "mafi" (nothing), "yalla" (let's go), "inshallah" (God willing — often signals uncertainty),
  "habibi/habibti" (dear), "m3 / متر مكعب" (cubic meter), "wین / wayn" (where)
- Numbers in Arabic: ١٢٣ = 123, ٠ = 0
- Voice note transcriptions appear as [TRANSCRIPTION: ...] markers — extract ALL intel from them

GEOGRAPHY — CRITICAL RULE:
- ALL projects and delivery sites are in LEBANON. There are no foreign locations.
- If any area, city, town, village, neighborhood, or district is mentioned — it is in Lebanon.
- Common Lebanese location keywords: منطقة (area/region), بلوك (block), مشروع (project),
  ورشة (construction site), موقع (site), حي (neighborhood)
- Scan EVERY message including voice note transcriptions for location mentions.
- Map vernacular names to standard: e.g. "trablous / طرابلس" → Tripoli,
  "sour / صور" → Tyre, "sayda / صيدا" → Saida, "jbeil / جبيل" → Jbeil
- Lebanese area taxonomy (all in Lebanon):
""" + ', '.join(AREA_TAXONOMY) + """

ChatChaos INTERNATIONAL BUSINESS CONTEXT:
- Products: ready-mix concrete, precast elements, concrete blocks, construction materials
- Volumes measured in cubic meters (m³ / متر مكعب / ميتر مكعب)
- Prices typically in USD (Lebanese economy is dollarized post-2019 crisis)
- Customers: contractors (مقاول), developers, project managers, distributors/dealers
- Delivery: ChatChaos delivers to construction sites; delivery scheduling is critical
- Mix specs: B250, B300, B350, B400; slump values (usually 10-16cm); additives; pump concrete
- "Kasser" / كسر = concrete strength test failure — CRITICAL urgency
- "Tarikh teslim" / تاريخ التسليم = delivery date — track carefully
- "Awamer" / أوامر = orders; "Kasra" = break/failure; "Tonn" = ton; "Meter mkaab" = m³
- Payment: most transactions in USD cash or bank transfer; LBP payments rare

CONTACT ROLES:
- Contractor / مقاول: executes construction work, orders concrete
- Developer / مطور: project owner/investor, approves large orders
- Project Manager / مهندس موقع: on-site manager, coordinates deliveries
- Dealer / وكيل: resells ChatChaos products, represents a region
- Architect / مهندس: designs projects, specifies mix grades
- Engineer: structural/civil engineer, approves specs

INSTRUCTIONS:
1. Extract ALL financial figures and volumes mentioned (even rough estimates)
2. Infer deal status from conversation tone and last messages
3. Mark urgency HIGH/CRITICAL for: unresolved complaints, delivery deadlines, test failures,
   payment disputes, or large pending orders
4. For primary_area: look in ALL messages. Only return null if truly no location mentioned.
5. For concrete_orders: extract each distinct order/quote as a separate entry.
6. For action_items: be specific with due dates when mentioned.
7. Output ONLY valid JSON — no markdown fences, no explanation text"""

USER_PROMPT_TEMPLATE = """Analyze this WhatsApp conversation export and return a JSON object.

CONVERSATION:
{conversation}

Return EXACTLY this JSON structure (no markdown, no extra text):
{{
  "chat_name": "inferred name of the contact or group",
  "primary_area": "single most relevant Lebanese delivery/project area or null",
  "secondary_areas": ["array of other areas mentioned"],
  "category": "Project | Contractor | Potential Client | Distributor | Internal/Team | Personal",
  "status": "Active | Waiting | Closed | Lost | Follow-up Needed",
  "urgency_level": "Low | Medium | High | Critical",
  "sentiment": "Positive | Neutral | Negative | Frustrated",
  "relationship_stage": "Cold | Warm | Hot | Negotiating | Confirmed | Delivered | Dispute",
  "language_mix": ["Arabic", "English", "French"],
  "executive_summary": "2-4 sentences in English summarising the conversation and commercial situation",
  "contact": {{
    "name": "full name extracted from messages or chat name",
    "phone": "phone number with country code if found, else null",
    "role": "Contractor | Developer | Project Manager | Dealer | Architect | Engineer | Unknown",
    "company": "company or firm name if mentioned, else null",
    "is_decision_maker": true
  }},
  "project": {{
    "name": "project name if mentioned, else null",
    "type": "Residential | Commercial | Infrastructure | Industrial | Unknown",
    "location_detail": "street, block, building name if mentioned, else null",
    "floors": null,
    "area_m2": null,
    "total_m3_estimate": null,
    "start_date": null,
    "completion_date": null
  }},
  "concrete_orders": [
    {{
      "mix_grade": "B250 | B300 | B350 | B400 or null",
      "slump": "slump value as string e.g. '14' or null",
      "pump_required": false,
      "volume_m3": 0.0,
      "price_per_m3": 0.0,
      "currency": "USD | LBP | EUR",
      "delivery_date": "YYYY-MM-DD or null",
      "status": "Quoted | Ordered | Delivered | Cancelled"
    }}
  ],
  "payment_info": {{
    "terms": "Cash | 30 days | 60 days | Credit | Unknown",
    "method": "Bank transfer | Cash | Check | Unknown",
    "outstanding_amount": null,
    "currency": "USD",
    "overdue": false
  }},
  "competitors_mentioned": ["array of competitor concrete supplier names"],
  "timeline": [
    {{"date": "YYYY-MM-DD", "event": "what happened"}}
  ],
  "financial_mentions": [
    {{
      "mention_date": "YYYY-MM-DD or null",
      "mention_type": "price_per_m3 | total_order | volume_m3 | quote | discount | delivery_cost | payment_terms | complaint | other",
      "amount": 0.0,
      "currency": "USD | LBP | EUR",
      "raw_text": "exact quote from conversation",
      "context_note": "brief interpretation"
    }}
  ],
  "negotiation_signals": ["array of signals like 'client asked for 5% discount on 200m3 order'"],
  "followup_needed": true,
  "followup_reason": "why follow-up is needed or null",
  "followup_action": "specific next step or null",
  "action_items": [
    {{
      "action": "specific actionable task",
      "due_date": "YYYY-MM-DD or null",
      "priority": "Low | Medium | High | Critical"
    }}
  ],
  "last_activity_date": "YYYY-MM-DD",
  "lifecycle_transitions": ["e.g. Lead on 2024-01-10 → Active on 2024-02-03"]
}}"""


# ── Gemini client ─────────────────────────────────────────────────────────────

def _get_client(api_key: Optional[str] = None):
    from google import genai
    key = (api_key or _API_KEY).strip()
    if not key:
        raise ValueError(
            "No Gemini API key found. Set GEMINI_API_KEY in .env.txt or paste it in the sidebar."
        )
    return genai.Client(api_key=key)


def analyze_chat(
    raw_text: str,
    chat_name: str = '',
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    import time
    from google.genai import types
    client = _get_client(api_key)
    conversation = _truncate(raw_text)
    if chat_name:
        conversation = f"[Chat name hint: {chat_name}]\n\n" + conversation

    prompt = USER_PROMPT_TEMPLATE.format(conversation=conversation)

    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=6000,
                    temperature=0.1,
                ),
            )
            return _parse_response(response.text.strip())
        except Exception as e:
            msg = str(e)
            if '429' in msg or 'RESOURCE_EXHAUSTED' in msg:
                # extract retry delay from error if present, else use backoff
                import re as _re
                m = _re.search(r'retry[^\d]*(\d+)', msg, _re.IGNORECASE)
                wait = int(m.group(1)) + 2 if m else (15 * (attempt + 1))
                if attempt < 3:
                    time.sleep(wait)
                    continue
            raise


def _parse_response(raw: str) -> Dict[str, Any]:
    cleaned = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', cleaned, re.DOTALL)
        try:
            data = json.loads(m.group()) if m else {}
        except json.JSONDecodeError:
            data = {}

    if 'primary_area' in data:
        data['primary_area'] = normalise_area(data.get('primary_area'))
    if isinstance(data.get('secondary_areas'), list):
        data['secondary_areas'] = [normalise_area(a) for a in data['secondary_areas'] if a]

    defaults = {
        'chat_name': '', 'primary_area': None, 'secondary_areas': [],
        'category': 'Contractor', 'status': 'Active', 'urgency_level': 'Low',
        'sentiment': 'Neutral', 'relationship_stage': 'Cold', 'language_mix': [],
        'executive_summary': 'Analysis unavailable.',
        'contact': {'name': None, 'phone': None, 'role': 'Unknown', 'company': None, 'is_decision_maker': False},
        'project': {'name': None, 'type': 'Unknown', 'location_detail': None, 'floors': None,
                    'area_m2': None, 'total_m3_estimate': None, 'start_date': None, 'completion_date': None},
        'concrete_orders': [],
        'payment_info': {'terms': 'Unknown', 'method': 'Unknown', 'outstanding_amount': None,
                         'currency': 'USD', 'overdue': False},
        'competitors_mentioned': [], 'timeline': [], 'financial_mentions': [],
        'negotiation_signals': [], 'followup_needed': False, 'followup_reason': None,
        'followup_action': None, 'action_items': [], 'last_activity_date': None,
        'lifecycle_transitions': [],
    }
    for k, v in defaults.items():
        data.setdefault(k, v)

    return data

