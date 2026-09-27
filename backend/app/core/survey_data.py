"""
Gamer DNA 20-Question Behavioral Question Bank.
Defines questions, options, and server-side scoring weights across 6 core dimensions:
Leadership, Communication, Strategy, Aggression, Teamwork, and Confidence.
"""

from typing import Any

# Question Bank with Server-Side Scoring Weights (Internal Only)
SURVEY_QUESTION_BANK: list[dict[str, Any]] = [
    # --------------------------------------------------------------------------
    # Leadership (4 Questions)
    # --------------------------------------------------------------------------
    {
        "id": "lead_01",
        "category": "Leadership",
        "question": "When team composition lacks critical synergy in the pre-match lobby, what is your instinct?",
        "options": [
            {"id": "lead_01_a", "text": "Step up, propose a clear synergistic comp, and guide role assignments.", "score": 100},
            {"id": "lead_01_b", "text": "Suggest gentle compromises to fill obvious gaps.", "score": 75},
            {"id": "lead_01_c", "text": "Quietly adapt and fill whatever role remains open.", "score": 50},
            {"id": "lead_01_d", "text": "Lock in my comfort pick and let the team figure it out in-game.", "score": 25},
        ],
    },
    {
        "id": "lead_02",
        "category": "Leadership",
        "question": "During a high-stakes match, your squad drops 3 consecutive rounds and morale wavers. How do you respond?",
        "options": [
            {"id": "lead_02_a", "text": "Call a tactical reset, identify the opponent's exploit, and establish the next round plan.", "score": 100},
            {"id": "lead_02_b", "text": "Keep energy positive with encouraging remarks and reminders to stay focused.", "score": 75},
            {"id": "lead_02_c", "text": "Mute chatter and concentrate solely on securing my own individual impact.", "score": 50},
            {"id": "lead_02_d", "text": "Vent frustration or check out mentally if the squad isn't listening.", "score": 20},
        ],
    },
    {
        "id": "lead_03",
        "category": "Leadership",
        "question": "In a frantic late-game standoff with no designated shotcaller, how do you handle calls?",
        "options": [
            {"id": "lead_03_a", "text": "Decisively voice the winning play and direct teammates on utility and target focus.", "score": 100},
            {"id": "lead_03_b", "text": "Voice clear suggestions while actively monitoring the minimap and timers.", "score": 75},
            {"id": "lead_03_c", "text": "Follow whoever speaks first or makes the first move.", "score": 50},
            {"id": "lead_03_d", "text": "Rely strictly on non-verbal in-game pings without speaking.", "score": 25},
        ],
    },
    {
        "id": "lead_04",
        "category": "Leadership",
        "question": "When an allied teammate begins tilting or struggling under intense match pressure:",
        "options": [
            {"id": "lead_04_a", "text": "Call an immediate mental reset, give them simple achievable tasks, and rebuild their focus.", "score": 100},
            {"id": "lead_04_b", "text": "Offer constructive encouragement and suggest swapping lanes or positions with them.", "score": 75},
            {"id": "lead_04_c", "text": "Play around their deficit quietly and focus on carrying without intervening.", "score": 50},
            {"id": "lead_04_d", "text": "Call out their mistakes publicly or tell them they are throwing the game.", "score": 20},
        ],
    },

    # --------------------------------------------------------------------------
    # Communication (3 Questions)
    # --------------------------------------------------------------------------
    {
        "id": "comm_01",
        "category": "Communication",
        "question": "How would you characterize your voice communication style during intense team encounters?",
        "options": [
            {"id": "comm_01_a", "text": "Crisp, concise, and continuous: exact coordinates, HP numbers, and enemy utility cooldowns.", "score": 100},
            {"id": "comm_01_b", "text": "Frequent callouts during engagements, keeping quiet between rounds.", "score": 75},
            {"id": "comm_01_c", "text": "Reserved communication; I speak primarily when asked or after I am eliminated.", "score": 50},
            {"id": "comm_01_d", "text": "Minimal or text-only comms; I prefer listening over talking.", "score": 25},
        ],
    },
    {
        "id": "comm_02",
        "category": "Communication",
        "question": "A teammate whiffs a pivotal ultimate or makes a costly mechanical error. What is your reaction?",
        "options": [
            {"id": "comm_02_a", "text": "Immediate verbal reset: 'Shake it off, nice try—here is our plan for the retake.'", "score": 100},
            {"id": "comm_02_b", "text": "Reassure them briefly to protect team morale and avoid tilt.", "score": 75},
            {"id": "comm_02_c", "text": "Stay silent to prevent awkwardness or conflict.", "score": 50},
            {"id": "comm_02_d", "text": "Spam question mark pings or question why they took that play.", "score": 15},
        ],
    },
    {
        "id": "comm_03",
        "category": "Communication",
        "question": "When a squadmate gives you direct feedback on your positioning during a match:",
        "options": [
            {"id": "comm_03_a", "text": "Actively incorporate the advice immediately and thank them for the vision.", "score": 100},
            {"id": "comm_03_b", "text": "Acknowledge the point calmly and evaluate its merit after the round.", "score": 75},
            {"id": "comm_03_c", "text": "Explain why I made the choice before agreeing to modify my play.", "score": 50},
            {"id": "comm_03_d", "text": "Feel irritated or mute their voice channel to avoid distraction.", "score": 20},
        ],
    },

    # --------------------------------------------------------------------------
    # Strategy (3 Questions)
    # --------------------------------------------------------------------------
    {
        "id": "strat_01",
        "category": "Strategy",
        "question": "Prior to executing on an objective, how thoroughly do you prepare your approach?",
        "options": [
            {"id": "strat_01_a", "text": "Thoroughly: bait enemy cooldowns, verify rotation timers, and layer utility.", "score": 100},
            {"id": "strat_01_b", "text": "Quick mental inventory of enemy ultimates and most dangerous angles.", "score": 75},
            {"id": "strat_01_c", "text": "React dynamically based on whatever first contact happens.", "score": 50},
            {"id": "strat_01_d", "text": "Just rush in; tactical overthinking causes hesitation.", "score": 25},
        ],
    },
    {
        "id": "strat_02",
        "category": "Strategy",
        "question": "The opposing team repeats a tricky aggressive flank pattern two rounds in a row:",
        "options": [
            {"id": "strat_02_a", "text": "Set up an anti-flank crossfire trap with coordinated utility to punish them.", "score": 100},
            {"id": "strat_02_b", "text": "Rotate our primary push to the opposite side of the map to avoid their trap.", "score": 75},
            {"id": "strat_02_c", "text": "Take the duel head-on at the same spot to prove mechanical superiority.", "score": 50},
            {"id": "strat_02_d", "text": "Ignore the pattern and hope a teammate holds that flank.", "score": 20},
        ],
    },
    {
        "id": "strat_03",
        "category": "Strategy",
        "question": "When a major patch changes balance, maps, or champion abilities:",
        "options": [
            {"id": "strat_03_a", "text": "Deep-dive patch analysis, review pro scrim vods, and lab novel synergies.", "score": 100},
            {"id": "strat_03_b", "text": "Play ranked matches and experiment hands-on to see what feels strongest.", "score": 75},
            {"id": "strat_03_c", "text": "Check community tier lists and follow popular influencer meta picks.", "score": 50},
            {"id": "strat_03_d", "text": "Disregard the meta completely and stick to my legacy comfort picks.", "score": 25},
        ],
    },

    # --------------------------------------------------------------------------
    # Aggression (3 Questions)
    # --------------------------------------------------------------------------
    {
        "id": "aggr_01",
        "category": "Aggression",
        "question": "At the start of an encounter or round, what is your preferred tempo?",
        "options": [
            {"id": "aggr_01_a", "text": "Immediate aggressive drive for space, pushing boundaries to seize first blood.", "score": 100},
            {"id": "aggr_01_b", "text": "Assertive forward contest of contested territory with protective utility.", "score": 75},
            {"id": "aggr_01_c", "text": "Measured default hold, waiting for opponents to overextend or make errors.", "score": 50},
            {"id": "aggr_01_d", "text": "Deep defensive containment, prioritizing survivability above all.", "score": 25},
        ],
    },
    {
        "id": "aggr_02",
        "category": "Aggression",
        "question": "You spot a weakened, fleeing enemy player near a dangerous choke point:",
        "options": [
            {"id": "aggr_02_a", "text": "Full dive and hunt them down; an eliminated enemy cannot stabilize.", "score": 100},
            {"id": "aggr_02_b", "text": "Flush them out with utility or coordinate a partner cut-off angle.", "score": 75},
            {"id": "aggr_02_c", "text": "Hold ground and secure the objective rather than risking a trade.", "score": 50},
            {"id": "aggr_02_d", "text": "Back off immediately in case their teammates are setting up a trap.", "score": 25},
        ],
    },
    {
        "id": "aggr_03",
        "category": "Aggression",
        "question": "Your team holds a commanding lead midway through the match. What is your mindset?",
        "options": [
            {"id": "aggr_03_a", "text": "Relentless pedal-to-the-metal aggression; suffocate them before they regroup.", "score": 100},
            {"id": "aggr_03_b", "text": "Maintain disciplined proactive offensive pressure while avoiding careless deaths.", "score": 75},
            {"id": "aggr_03_c", "text": "Slow down pace, play conservative setups, and bleed the round clock.", "score": 50},
            {"id": "aggr_03_d", "text": "Play super passive and let them dictate the pace of every skirmish.", "score": 25},
        ],
    },

    # --------------------------------------------------------------------------
    # Teamwork (3 Questions)
    # --------------------------------------------------------------------------
    {
        "id": "team_01",
        "category": "Teamwork",
        "question": "You have excess resources/credits, but an essential teammate is resource-starved:",
        "options": [
            {"id": "team_01_a", "text": "Instantly purchase their full loadout even if it forces me onto a secondary weapon.", "score": 100},
            {"id": "team_01_b", "text": "Coordinate a mutual budget buy so both of us have adequate utility.", "score": 75},
            {"id": "team_01_c", "text": "Drop a weapon for them only if their current score justifies the investment.", "score": 50},
            {"id": "team_01_d", "text": "Prioritize my own max loadout first; they should manage their own economy.", "score": 25},
        ],
    },
    {
        "id": "team_02",
        "category": "Teamwork",
        "question": "In team battles, what is your default positioning and objective focus?",
        "options": [
            {"id": "team_02_a", "text": "Anchor near vulnerable teammates, ready to peel, flash, or trade their elimination.", "score": 100},
            {"id": "team_02_b", "text": "Set up a synchronized crossfire angle with an allied player.", "score": 75},
            {"id": "team_02_c", "text": "Take a separate individual flank to surprise adversaries.", "score": 50},
            {"id": "team_02_d", "text": "Bait teammates' positioning to secure clean cleanup eliminations.", "score": 20},
        ],
    },
    {
        "id": "team_03",
        "category": "Teamwork",
        "question": "The squad votes for an unconventional, risky strategy that you personally doubt:",
        "options": [
            {"id": "team_03_a", "text": "Commit 100% to the execution; a synchronized flawed plan beats a disjointed good one.", "score": 100},
            {"id": "team_03_b", "text": "Voice my concern once, but execute my assigned role faithfully.", "score": 75},
            {"id": "team_03_c", "text": "Soft-commit while holding an escape route for when things go south.", "score": 45},
            {"id": "team_03_d", "text": "Refuse to participate and run my own proven solo tactic.", "score": 15},
        ],
    },

    # --------------------------------------------------------------------------
    # Confidence (4 Questions)
    # --------------------------------------------------------------------------
    {
        "id": "conf_01",
        "category": "Confidence",
        "question": "You find yourself in a 1v3 clutch situation on match point with the entire lobby spectating you:",
        "options": [
            {"id": "conf_01_a", "text": "Thrive under the pressure, isolate 1v1 duels with supreme confidence, and play to win.", "score": 100},
            {"id": "conf_01_b", "text": "Remain composed and stick to standard clutch fundamentals to maximize winning odds.", "score": 75},
            {"id": "conf_01_c", "text": "Feel nervous and second-guess decisions, worried about letting the squad down.", "score": 50},
            {"id": "conf_01_d", "text": "Save equipment or concede early to avoid the embarrassment of failing the clutch.", "score": 25},
        ],
    },
    {
        "id": "conf_02",
        "category": "Confidence",
        "question": "You are matched against a renowned high-tier or top-ranked opponent in your direct lane/duel:",
        "options": [
            {"id": "conf_02_a", "text": "Welcome the challenge enthusiastically, confident I can outplay them on any given day.", "score": 100},
            {"id": "conf_02_b", "text": "Play with heightened focus and respect their skill while testing their weaknesses.", "score": 75},
            {"id": "conf_02_c", "text": "Adopt an ultra-defensive posture, intimidated by their rank and reputation.", "score": 50},
            {"id": "conf_02_d", "text": "Accept defeat mentally before first contact and blame the matchmaking algorithm.", "score": 20},
        ],
    },
    {
        "id": "conf_03",
        "category": "Confidence",
        "question": "Following a sequence of missed shots or poorly executed plays in the first half:",
        "options": [
            {"id": "conf_03_a", "text": "Instant mental wipe: I maintain unwavering belief in my mechanical aim and instincts.", "score": 100},
            {"id": "conf_03_b", "text": "Take a deep breath between rounds, refocus on crosshair placement, and rebuild rhythm.", "score": 75},
            {"id": "conf_03_c", "text": "Hesitate on subsequent duels, fearing another costly mechanical whiff.", "score": 50},
            {"id": "conf_03_d", "text": "Spiral into tilt, losing all confidence in my ability to hit targets for the match.", "score": 20},
        ],
    },
    {
        "id": "conf_04",
        "category": "Confidence",
        "question": "Your squad needs one player to execute a high-risk, game-deciding play to secure victory:",
        "options": [
            {"id": "conf_04_a", "text": "Vocalize immediately: 'Put it on me, I will make the play happen.'", "score": 100},
            {"id": "conf_04_b", "text": "Step up willingly if designated, executing the gameplan with quiet determination.", "score": 75},
            {"id": "conf_04_c", "text": "Hope someone else volunteers so the outcome doesn't rest squarely on my shoulders.", "score": 50},
            {"id": "conf_04_d", "text": "Actively refuse the responsibility to avoid taking the blame if the round fails.", "score": 20},
        ],
    },
]

# Fast indexed lookups
_QUESTIONS_MAP: dict[str, dict[str, Any]] = {q["id"]: q for q in SURVEY_QUESTION_BANK}
_OPTIONS_MAP: dict[str, dict[str, Any]] = {}
for q in SURVEY_QUESTION_BANK:
    for opt in q["options"]:
        _OPTIONS_MAP[opt["id"]] = {
            "question_id": q["id"],
            "category": q["category"],
            "text": opt["text"],
            "score": opt["score"],
        }


def get_all_questions_public() -> list[dict[str, Any]]:
    """
    Returns the complete list of 20 questions WITHOUT scoring weights.
    Protects algorithmic scoring integrity on client delivery.
    """
    public_questions = []
    for q in SURVEY_QUESTION_BANK:
        public_questions.append({
            "id": q["id"],
            "category": q["category"],
            "question": q["question"],
            "options": [
                {"id": opt["id"], "text": opt["text"]}
                for opt in q["options"]
            ],
        })
    return public_questions


def get_question_by_id(question_id: str) -> dict[str, Any] | None:
    """Retrieve full question detail with options."""
    return _QUESTIONS_MAP.get(question_id)


def get_option_evaluation(option_id: str) -> dict[str, Any] | None:
    """Retrieve option scoring metadata and category."""
    return _OPTIONS_MAP.get(option_id)
