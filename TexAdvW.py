import asyncio
import json
import random
from reactpy import component, html, use_state, use_effect
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# --- Types & Initial State ---
INITIAL_PLAYER = {
    "hp": 21,
    "gold": 0,
    "weapon": "none",
    "helmet": "none",
    "weaponNameStr": "",
    "helmetNameStr": "",
    "inventory": []
}

def weapon_name(p):
    if p["weapon"] == "none":
        return "無"
    base_name = p["weaponNameStr"] or "武器"
    return f"初級 {base_name}" if p["weapon"] == "basic" else f"高級 {base_name}"

def helmet_name(p):
    if p["helmet"] == "none":
        return "無"
    base_name = p["helmetNameStr"] or "頭盔"
    return f"初級 {base_name}" if p["helmet"] == "basic" else f"高級 {base_name}"

# --- Pydantic Schemas for Structured Output ---
class Room1Choice(BaseModel):
    location: str = Field(description="位置描述，例如：看起來像是十年沒整理的書桌")
    itemType: str = Field(description="物品種類，必須是 'weapon', 'helmet', 或 'other'")
    itemName: str = Field(description="物品名稱，例如：洞爺湖")
    outcomeText: str = Field(description="獲得物品時的幽默描述")

class Room1Response(BaseModel):
    description: str = Field(description="房間的幽默描述")
    choices: list[Room1Choice]

class Room3Response(BaseModel):
    description: str = Field(description="NPC的描述與對話")
    emoji: str = Field(description="代表該NPC的Emoji")

class Room4Response(BaseModel):
    dialogue: str = Field(description="工匠的吐槽與歡迎台詞")

# --- Components ---

@component
def Scene(emoji, text, choices, bossHp=None, bossMaxHp=None):
    choice_buttons = []
    for i, c in enumerate(choices):
        disabled = c.get("disabled", False)
        btn = html.button(
            {
                "key": i,
                "on_click": c["onClick"] if not disabled else lambda e: None,
                "disabled": disabled,
                "style": {
                    "display": "block",
                    "width": "100%",
                    "padding": "10px",
                    "margin_bottom": "10px",
                    "background_color": "#333" if not disabled else "#555",
                    "color": "white" if not disabled else "#999",
                    "border": "2px solid white",
                    "cursor": "pointer" if not disabled else "not-allowed",
                    "text_align": "left",
                    "font_family": "monospace"
                }
            },
            c["label"]
        )
        choice_buttons.append(btn)

    boss_bar = ""
    if bossHp is not None and bossMaxHp is not None:
        hp_percent = max(0, (bossHp / bossMaxHp) * 100)
        boss_bar = html.div(
            {"style": {"width": "100%", "max_width": "300px", "margin_bottom": "20px"}},
            html.div(
                {"style": {"display": "flex", "justify_content": "space-between", "margin_bottom": "5px"}},
                html.span("😈 Boss HP"),
                html.span(f"{bossHp} / {bossMaxHp}")
            ),
            html.div(
                {"style": {"height": "24px", "border": "4px solid white", "background_color": "black", "padding": "2px"}},
                html.div(
                    {"style": {"height": "100%", "background_color": "red", "width": f"{hp_percent}%", "transition": "width 0.3s"}}
                )
            )
        )

    return html.div(
        {"style": {"display": "flex", "flex_direction": "column", "flex": "1", "height": "100%"}},
        html.div(
            {"style": {"flex": "1", "display": "flex", "flex_direction": "column", "align_items": "center", "justify_content": "center", "padding": "20px"}},
            html.div({"style": {"font_size": "80px", "margin_bottom": "20px"}}, emoji),
            boss_bar if boss_bar else ""
        ),
        html.div(
            {"style": {"border_top": "4px solid white", "padding_top": "20px", "margin_top": "auto"}},
            html.div(
                {"style": {"margin_bottom": "20px", "white_space": "pre-wrap", "line_height": "1.5", "max_height": "200px", "overflow_y": "auto"}},
                text
            ),
            html.div(
                {"style": {"display": "flex", "flex_direction": "column", "gap": "10px"}},
                *choice_buttons
            )
        )
    )

@component
def TitleScreen(onStart, achievements, api_key, set_api_key):
    is_loading, set_is_loading = use_state(False)
    error_msg, set_error_msg = use_state("")

    async def handle_start(e):
        if not api_key:
            set_error_msg("請輸入 API Key")
            return
        
        set_is_loading(True)
        set_error_msg("")
        try:
            client = genai.Client(api_key=api_key)
            # 輕量 API 請求測試 Key 是否合法
            await client.aio.models.generate_content(
                model='gemini-3-flash-preview',
                contents='test'
            )
            onStart()
        except Exception as ex:
            set_error_msg(f"API Key 驗證失敗: {str(ex)}")
            set_is_loading(False)

    achievements_display = ""
    if achievements:
        achievements_display = html.div(
            {"style": {"margin_top": "40px", "border_top": "4px solid white", "padding_top": "20px", "text_align": "left", "width": "100%"}},
            html.h3({"style": {"color": "gold", "margin_bottom": "10px"}}, "🏆 已解鎖成就："),
            html.div(
                {"style": {"display": "flex", "flex_wrap": "wrap", "gap": "10px"}},
                *[html.span({"style": {"background_color": "#333", "border": "2px solid #666", "padding": "5px 10px"}}, a) for a in achievements]
            )
        )

    return html.div(
        {"style": {"display": "flex", "flex_direction": "column", "align_items": "center", "justify_content": "center", "flex": "1", "text_align": "center", "padding": "40px 0"}},
        html.h1({"style": {"font_size": "40px", "margin_bottom": "20px"}}, "命運的十字路口"),
        html.div({"style": {"font_size": "60px", "margin_bottom": "40px"}}, "🗡️"),
        
        html.div(
            {"style": {"width": "100%", "max_width": "300px", "display": "flex", "flex_direction": "column", "gap": "10px", "text_align": "left", "margin_bottom": "20px"}},
            html.label({"style": {"font_size": "14px", "color": "#ccc"}}, "Gemini API Key"),
            html.input({
                "type": "password",
                "value": api_key,
                "on_change": lambda e: set_api_key(e["target"]["value"]),
                "placeholder": "輸入 API Key...",
                "style": {"background_color": "black", "border": "2px solid white", "color": "white", "padding": "10px", "font_family": "monospace", "width": "100%", "box_sizing": "border-box"}
            }),
            html.div({"style": {"color": "red", "font_size": "14px"}}, error_msg) if error_msg else ""
        ),

        html.button(
            {
                "on_click": handle_start,
                "disabled": is_loading,
                "style": {"padding": "15px 30px", "font_size": "20px", "background_color": "#333", "color": "white", "border": "2px solid white", "cursor": "pointer" if not is_loading else "wait"}
            },
            "驗證中..." if is_loading else "開始遊戲"
        ),
        achievements_display
    )

@component
def Room1(onNext, player, setPlayer, api_key):
    loading, set_loading = use_state(True)
    scene_data, set_scene_data = use_state(None)
    step, set_step = use_state(0)
    outcome, set_outcome = use_state("")
    outcome_item, set_outcome_item = use_state(None)
    choices_made, set_choices_made = use_state(0)
    selected_indices, set_selected_indices = use_state(set())

    @use_effect(dependencies=[])
    async def fetch_scene():
        try:
            client = genai.Client(api_key=api_key)
            response = await client.aio.models.generate_content(
                model='gemini-3-flash-preview',
                contents="玩家現在在Room1[神秘的石室]，隨機生成三個位置說明選項並隨機生成獲得物品，物品必須為：1.武器類、2.防具類、3.任意類別(非武器或防具，可為食物、書籍或任何無相關物品)。可引用知名漫畫、影視、文學內武器與防具，如：洞爺湖、斬魄刀、破魔之矢，不限形式，不一定要是刀具類武器。例如：看起來像是十年沒整理的書桌。選擇後出現：找到一把斬破刀。以幽默有趣的方式描述，並且要能讓玩家產生共鳴，如貼近生活場景或引用大眾話題。務必避免引用有爭議、敏感、涉及暴力或色情的話題。",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Room1Response,
                    temperature=0.9, # 增加隨機性
                    top_p=0.95
                )
            )
            data = json.loads(response.text)
            set_scene_data(data)
        except Exception as e:
            print("Error:", e)
            set_scene_data({
                "description": "【神秘的石室】\n你解開了牆上的拼圖，寶箱應聲而開！",
                "choices": [
                    {"location": "左邊的寶箱", "itemType": "weapon", "itemName": "初級武器", "outcomeText": "獲得物品：[初級武器]"},
                    {"location": "右邊的寶箱", "itemType": "helmet", "itemName": "初級頭盔", "outcomeText": "獲得物品：[初級頭盔]"},
                    {"location": "中間的寶箱", "itemType": "other", "itemName": "神秘垃圾", "outcomeText": "獲得物品：[神秘垃圾]"}
                ]
            })
        finally:
            set_loading(False)

    def handle_choice(choice, index):
        def update_player(p):
            np = p.copy()
            if choice["itemType"] == 'weapon':
                np["weapon"] = 'basic'
                np["weaponNameStr"] = choice["itemName"]
            elif choice["itemType"] == 'helmet':
                np["helmet"] = 'basic'
                np["helmetNameStr"] = choice["itemName"]
            else:
                np["inventory"] = np["inventory"] + [choice["itemName"]]
            return np
        
        setPlayer(update_player)
        set_outcome(choice["outcomeText"])
        set_outcome_item(choice)
        
        new_indices = set(selected_indices)
        new_indices.add(index)
        set_selected_indices(new_indices)
        
        set_choices_made(choices_made + 1)
        set_step(1)

    if loading:
        return Scene(emoji="⏳", text="正在適應眼前的景色...", choices=[])

    if step == 0:
        choices = []
        for i, c in enumerate(scene_data["choices"]):
            choices.append({
                "label": f"[{i+1}] 探索 {c['location']}",
                "onClick": lambda event, c=c, i=i: handle_choice(c, i),
                "disabled": i in selected_indices
            })
        return Scene(emoji="🧰", text=scene_data["description"], choices=choices)

    item_emoji = '⚔️' if outcome_item and outcome_item.get('itemType') == 'weapon' else '🛡️' if outcome_item and outcome_item.get('itemType') == 'helmet' else '📦'
    item_type_str = 'WEAPON' if outcome_item and outcome_item.get('itemType') == 'weapon' else 'ARMOR' if outcome_item and outcome_item.get('itemType') == 'helmet' else 'ITEM'
    
    return html.div(
        {"style": {"display": "flex", "flex_direction": "column", "flex": "1", "height": "100%"}},
        html.div(
            {"style": {"flex": "1", "display": "flex", "flex_direction": "column", "align_items": "center", "justify_content": "center", "padding": "20px"}},
            html.div({"style": {"font_size": "60px", "margin_bottom": "20px"}}, "✨"),
            html.div(
                {"style": {"border": "4px solid white", "padding": "20px", "display": "flex", "flex_direction": "column", "align_items": "center", "justify_content": "center", "width": "200px", "height": "200px", "background_color": "#222", "margin_bottom": "20px"}},
                html.div({"style": {"font_size": "60px", "margin_bottom": "10px"}}, item_emoji),
                html.div({"style": {"font_size": "18px", "font_weight": "bold", "text_align": "center", "border": "2px solid white", "padding": "5px", "width": "100%", "overflow": "hidden", "text_overflow": "ellipsis", "white_space": "nowrap"}}, outcome_item.get("itemName", "") if outcome_item else ""),
                html.div({"style": {"font_size": "12px", "color": "#aaa", "margin_top": "10px"}}, item_type_str)
            )
        ),
        html.div(
            {"style": {"border_top": "4px solid white", "padding_top": "20px", "margin_top": "auto"}},
            html.div({"style": {"margin_bottom": "20px", "white_space": "pre-wrap", "line_height": "1.5"}}, outcome),
            html.div(
                {"style": {"display": "flex", "flex_direction": "column", "gap": "10px"}},
                html.button(
                    {
                        "on_click": lambda e: set_step(0) if choices_made < 2 else onNext(),
                        "style": {"padding": "10px", "background_color": "#333", "color": "white", "border": "2px solid white", "cursor": "pointer", "text_align": "left"}
                    },
                    "繼續探索房間" if choices_made < 2 else "繼續前進"
                )
            )
        )
    )

@component
def Room2(onNext, player, setPlayer):
    step, set_step = use_state(0)
    result_text, set_result_text = use_state("")

    def handle_choice(choice):
        if choice == 1:
            set_result_text("⚔️ 敵人被你擊敗了！哥布林應聲倒地。")
        elif choice == 2:
            set_result_text("🗣️ 敵人被你機掰了！哥布林羞愧地掩面逃跑。")
        elif choice == 3:
            set_result_text("💔 敵人成為心碎小狗！哥布林覺得被冷落，哭著跑走了。")
        
        def update_player(p):
            np = p.copy()
            np["gold"] += 10
            return np
        setPlayer(update_player)
        set_step(1)

    if step == 0:
        return Scene(
            emoji="👺",
            text="【誰被綁架了！】\n你看到一隻哥布林正在威脅一名商人！\n你要如何應對？",
            choices=[
                {"label": f"[1] 使用 武器 ({weapon_name(player)})", "onClick": lambda e: handle_choice(1), "disabled": player["weapon"] == 'none'},
                {"label": "[2] 使用 嘴遁", "onClick": lambda e: handle_choice(2)},
                {"label": "[3] 使用 無視", "onClick": lambda e: handle_choice(3)}
            ]
        )

    return Scene(
        emoji="💰",
        text=f"{result_text}\n\n商人得救了，感激涕零地塞了一袋錢給你。\n獲得金幣：10 枚",
        choices=[{"label": "繼續前進", "onClick": lambda e: onNext()}]
    )

@component
def Room3(onNext, player, setPlayer, addAchievement, api_key):
    loading, set_loading = use_state(True)
    npc_data, set_npc_data = use_state(None)
    step, set_step = use_state(0)
    result_text, set_result_text = use_state("")

    @use_effect(dependencies=[])
    async def fetch_npc():
        try:
            client = genai.Client(api_key=api_key)
            response = await client.aio.models.generate_content(
                model='gemini-3-flash-preview',
                contents="玩家現在在Room3[人性的考驗]，隨機生成NPC名稱、狀態，且對話方式符合其名稱和狀態。如：一個[畫著藍色眼影]的[囂張大嬸]攔住你，語氣傲慢：「[小鬼]，買支愛心筆吧！只要 5 枚金幣，[很便宜你了吧？]」([]內為替換部分)。注意：愛心筆的價格務必固定為 5 枚金幣，不可更改。",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Room3Response,
                    temperature=0.9, # 增加隨機性
                    top_p=0.95
                )
            )
            data = json.loads(response.text)
            set_npc_data(data)
        except Exception as e:
            print("Error:", e)
            set_npc_data({
                "description": "一個衣衫襤褸的 老人 攔住你：「勇者，買支愛心筆吧！只要 5 枚金幣...」",
                "emoji": "🧙‍♂️"
            })
        finally:
            set_loading(False)

    def handle_choice(choice):
        if choice == 1:
            def update_player(p):
                np = p.copy()
                np["gold"] -= 5
                np["inventory"] = np["inventory"] + ["愛心筆"]
                return np
            setPlayer(update_player)
            addAchievement('好人一生平安')
            set_result_text("你花費了 5 枚金幣，獲得了『愛心筆』。")
        elif choice == 2:
            addAchievement('反詐專家')
            set_result_text("你冷漠地拒絕了，對方悻悻然地離開。")
        elif choice == 3:
            addAchievement('清澈的眼神')
            set_result_text("你假裝沒看到，默默繞了過去。")
        set_step(1)

    if loading:
        return Scene(emoji="⏳", text="前方似乎有個人影...", choices=[])

    if step == 0:
        return Scene(
            emoji=npc_data["emoji"],
            text=f"【人性的考驗】\n{npc_data['description']}\n(你目前有 {player['gold']} 枚金幣)",
            choices=[
                {"label": "[1] 捨我其誰 (錢包君-5滴血)", "onClick": lambda e: handle_choice(1), "disabled": player["gold"] < 5},
                {"label": "[2] 冷漠拒絕", "onClick": lambda e: handle_choice(2)},
                {"label": "[3] 看向遠方", "onClick": lambda e: handle_choice(3)}
            ]
        )

    return Scene(
        emoji="🚶",
        text=f"[勇者，你已做出選擇]\n\n{result_text}",
        choices=[{"label": "繼續前進", "onClick": lambda e: onNext()}]
    )

@component
def Room4(onNext, player, setPlayer, api_key):
    loading, set_loading = use_state(True)
    text, set_text = use_state("")

    @use_effect(dependencies=[])
    async def fetch_dialogue():
        try:
            client = genai.Client(api_key=api_key)
            wName = player["weaponNameStr"] or ('空手' if player["weapon"] == 'none' else '初級武器')
            hName = player["helmetNameStr"] or ('沒戴頭盔' if player["helmet"] == 'none' else '初級頭盔')
            
            response = await client.aio.models.generate_content(
                model='gemini-3-flash-preview',
                contents=f"玩家現在在Room4[神秘附魔工坊]，工匠根據玩家持有的武器、防具裝備進行相關吐槽再附魔(升級)。玩家目前武器：【{wName}】，防具：【{hName}】。請以幽默有趣的方式描述，並且要能讓玩家產生共鳴。務必避免引用有爭議、敏感、涉及暴力或色情的話題。",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Room4Response
                )
            )
            data = json.loads(response.text)
            set_text(f"【暗黑工坊】\n{data['dialogue']}\n\n工匠說：「我可以幫你升級裝備，每升級一項需要 5 枚金幣。」")
        except Exception as e:
            print("Error:", e)
            set_text("【暗黑工坊】\n工匠說：「我可以幫你升級裝備，每升級一項需要 5 枚金幣。」")
        finally:
            set_loading(False)

    def upgrade_weapon(e):
        def update_player(p):
            np = p.copy()
            np["gold"] -= 5
            np["weapon"] = 'high'
            return np
        setPlayer(update_player)
        wName = player["weaponNameStr"] or '武器'
        set_text(f"✨ 武器已升級為 [高級 {wName}]！\n\n工匠說：「還需要升級什麼嗎？」")

    def upgrade_helmet(e):
        def update_player(p):
            np = p.copy()
            np["gold"] -= 5
            np["helmet"] = 'high'
            return np
        setPlayer(update_player)
        hName = player["helmetNameStr"] or '頭盔'
        set_text(f"✨ 頭盔已升級為 [高級 {hName}]！\n\n工匠說：「還需要升級什麼嗎？」")

    if loading:
        return Scene(emoji="⏳", text="工匠正在打量你的裝備...", choices=[])

    return Scene(
        emoji="⚒️",
        text=text,
        choices=[
            {"label": "[1] 升級為高級武器 (5金幣)", "onClick": upgrade_weapon, "disabled": player["gold"] < 5 or player["weapon"] == 'high' or player["weapon"] == 'none'},
            {"label": "[2] 升級為高級頭盔 (5金幣)", "onClick": upgrade_helmet, "disabled": player["gold"] < 5 or player["helmet"] == 'high' or player["helmet"] == 'none'},
            {"label": "[3] 什麼都不升級，直接離開", "onClick": lambda e: onNext()}
        ]
    )

@component
def Room5(onVictory, onGameOver, player, setPlayer):
    boss_hp, set_boss_hp = use_state(24)
    logs, set_logs = use_state(["【魔王降臨】\n深淵魔王出現了！"])
    is_ending, set_is_ending = use_state(False)

    async def attack(e):
        if player["hp"] < 3 and '愛心筆' in player["inventory"]:
            set_logs(logs + ["🌟 【觸發隱藏機制】 🌟\n你背包裡的『愛心筆』突然發出刺眼的光芒，變成了【強制愛心筆】！\n你自動發動了絕招【強迫推銷】！Boss 無法承受這股可怕的精神壓力，崩潰了！"])
            set_boss_hp(0)
            set_is_ending(True)
            await asyncio.sleep(3)
            onVictory()
            return

        # 玩家攻擊階段
        player_dmg = 6 if player["weapon"] == 'high' else (4 if player["weapon"] == 'basic' else 1)
        new_boss_hp = max(0, boss_hp - player_dmg)
        set_boss_hp(new_boss_hp)
        
        new_logs = [f"⚔️ 你對 Boss 造成了 {player_dmg} 點傷害。"]
        
        if new_boss_hp <= 0:
            set_logs(logs + new_logs + ["🎉 恭喜過關！你成功走出了迷宮！"])
            set_is_ending(True)
            await asyncio.sleep(3)
            onVictory()
            return

        # 魔王攻擊階段
        boss_atk = random.randint(4, 7)
        
        # 新增規則：若玩家持有高級頭盔，魔王有 10% 機率無視防禦
        ignore_def = False
        if player["helmet"] == 'high':
            if random.random() < 0.10: # 10% 機率
                ignore_def = True
                player_def = 0
            else:
                player_def = 3
        else:
            player_def = 1 if player["helmet"] == 'basic' else 0
            
        actual_dmg = max(0, boss_atk - player_def)
        
        new_hp = player["hp"] - actual_dmg
        
        def update_player(p):
            np = p.copy()
            np["hp"] = new_hp
            return np
            
        setPlayer(update_player)
        
        if ignore_def:
            new_logs.append(f"⚠️ 警告！魔王發動了【無視防禦】！你的高級頭盔未能抵擋，受到 {actual_dmg} 點真實傷害。")
        else:
            new_logs.append(f"🛡️ Boss 攻擊了你！頭盔抵擋了 {player_def} 點傷害，你受到 {actual_dmg} 點實際傷害。")
            
        set_logs(logs + new_logs)

        if new_hp <= 0:
            set_is_ending(True)
            await asyncio.sleep(3)
            onGameOver()

    return Scene(
        emoji="💀" if boss_hp <= 0 else "😈",
        text="\n\n".join(logs),
        choices=[
            {"label": "👉 進行攻擊", "onClick": attack, "disabled": is_ending or player["hp"] <= 0 or boss_hp <= 0}
        ],
        bossHp=boss_hp,
        bossMaxHp=20
    )

@component
def EndScreen(onRestart, achievements, player):
    is_victory = player["hp"] > 0
    
    achievements_display = ""
    if achievements:
        achievements_display = html.div(
            {"style": {"margin_top": "20px", "border_top": "4px solid white", "padding_top": "20px", "text_align": "left", "width": "100%"}},
            html.h3({"style": {"color": "gold", "margin_bottom": "10px"}}, "🏆 當前成就總覽"),
            html.div(
                {"style": {"display": "flex", "flex_wrap": "wrap", "gap": "10px"}},
                *[html.span({"style": {"background_color": "#333", "border": "2px solid #666", "padding": "5px 10px"}}, a) for a in achievements]
            )
        )
    else:
        achievements_display = html.div(
            {"style": {"margin_top": "20px", "border_top": "4px solid white", "padding_top": "20px", "text_align": "left", "width": "100%"}},
            html.h3({"style": {"color": "gold", "margin_bottom": "10px"}}, "🏆 當前成就總覽"),
            html.p({"style": {"color": "#aaa"}}, "無")
        )

    return html.div(
        {"style": {"display": "flex", "flex_direction": "column", "align_items": "center", "justify_content": "center", "flex": "1", "text_align": "center", "padding": "40px 0"}},
        html.h1({"style": {"font_size": "40px", "color": "gold" if is_victory else "red", "margin_bottom": "20px"}}, "🎉 遊戲通關 🎉" if is_victory else "☠️ 遊戲結束 ☠️"),
        html.div({"style": {"font_size": "80px", "margin_bottom": "20px"}}, "👑" if is_victory else "🪦"),
        html.div({"style": {"font_size": "20px", "margin_bottom": "20px"}}, "恭喜你成功走出了迷宮！" if is_victory else "你被 Boss 擊敗了..."),
        achievements_display,
        html.button(
            {
                "on_click": lambda e: onRestart(),
                "style": {"margin_top": "40px", "padding": "15px 30px", "font_size": "20px", "background_color": "#333", "color": "white", "border": "2px solid white", "cursor": "pointer", "width": "100%"}
            },
            "🔄 重新開始"
        )
    )

@component
def App():
    game_state, set_game_state = use_state("title")
    player, set_player = use_state(INITIAL_PLAYER)
    achievements, set_achievements = use_state(set())
    api_key, set_api_key = use_state("")

    def add_achievement(ach):
        new_achievements = set(achievements)
        new_achievements.add(ach)
        set_achievements(new_achievements)

    def start_game(is_restart=False):
        set_player(INITIAL_PLAYER)
        set_game_state("room1")
        if is_restart:
            add_achievement("穢土轉生")

    content = ""
    if game_state == "title":
        content = TitleScreen(lambda: start_game(False), achievements, api_key, set_api_key)
    elif game_state == "room1":
        content = Room1(lambda: set_game_state("room2"), player, set_player, api_key)
    elif game_state == "room2":
        content = Room2(lambda: set_game_state("room3"), player, set_player)
    elif game_state == "room3":
        content = Room3(lambda: set_game_state("room4"), player, set_player, add_achievement, api_key)
    elif game_state == "room4":
        content = Room4(lambda: set_game_state("room5"), player, set_player, api_key)
    elif game_state == "room5":
        content = Room5(
            lambda: [add_achievement("大難不死"), set_game_state("end")],
            lambda: [add_achievement("終有一死"), set_game_state("end")],
            player, set_player
        )
    elif game_state == "end":
        content = EndScreen(lambda: start_game(True), achievements, player)

    header = ""
    if game_state != "title":
        inventory_str = ", ".join(player["inventory"]) if player["inventory"] else "無"
        header = html.div(
            {"style": {"display": "flex", "flex_wrap": "wrap", "gap": "20px", "justify_content": "space-between", "border": "4px solid white", "padding": "15px", "margin_bottom": "20px", "background_color": "black"}},
            html.div(f"❤️ HP: {player['hp']}"),
            html.div(f"💰 金幣: {player['gold']}"),
            html.div(f"⚔️ 武器: {weapon_name(player)}"),
            html.div(f"🛡️ 頭盔: {helmet_name(player)}"),
            html.div({"style": {"width": "100%", "margin_top": "10px", "padding_top": "10px", "border_top": "2px dashed #666"}}, f"🎒 物品: {inventory_str}")
        )

    return html.div(
        {"style": {"min_height": "100vh", "background_color": "#111", "color": "white", "font_family": "monospace", "display": "flex", "flex_direction": "column", "align_items": "center", "padding": "20px"}},
        html.div(
            {"style": {"width": "100%", "max_width": "600px"}},
            header,
            html.div(
                {"style": {"border": "4px solid white", "padding": "20px", "min_height": "500px", "display": "flex", "flex_direction": "column", "background_color": "black"}},
                content
            )
        )
    )

if __name__ == "__main__":
    import os
    from reactpy import run
    
    # 動態讀取雲端環境提供的 PORT，若無則預設使用 8000
    port = int(os.environ.get("PORT", 8000))
    
    print(f"伺服器啟動中... 綁定 Port: {port}")
    # 必須將 host 設為 "0.0.0.0"，雲端平台的路由才能正確把玩家導向你的遊戲
    run(App, host="0.0.0.0", port=port)