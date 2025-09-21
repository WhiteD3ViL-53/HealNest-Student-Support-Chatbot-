# mental.py — Heal Nest (User dashboard with Resources Hub — improved metadata & fixed Streamlit call)
# Save to: C:\Users\SIDDHANT THAKUR\Desktop\weatherapp\mental.py

import os
from datetime import datetime
import secrets
import string

import streamlit as st
import streamlit.components.v1 as components

from data_store_utils import load_data, save_data

# -----------------------
# Page config + CSS
# -----------------------
st.set_page_config(page_title="Heal Nest — Student", layout="wide")
st.markdown(
    """
    <style>
    :root{--bg:#081026;--card:#0b1220;--muted:#cfe8ff;--accent:#173247}
    body { background-color: var(--bg); color: #e6eef8; }
    .cards-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 28px; align-items:stretch; }
    .ms-card { background: linear-gradient(180deg, rgba(11,18,32,0.95), rgba(6,10,18,0.95)); border-radius:18px; padding:26px; box-shadow: 0 12px 34px rgba(0,0,0,0.55); color: #e6eef8; min-height:220px; display:flex; flex-direction:column; justify-content:space-between; }
    .ms-card h2 { margin:0 0 8px 0; font-size:20px; }
    .ms-card p { margin:0; color:#c9d6ea; font-size:14px }
    .resource-grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:18px; }
    .resource-card { background:#071021; border-radius:14px; padding:18px; min-height:140px; box-shadow: 0 8px 20px rgba(0,0,0,0.5); }
    .resource-title { font-size:16px; font-weight:700; color:#e6eef8; margin-bottom:6px; }
    .resource-desc { color:#bcd6ef; font-size:13px; margin-bottom:8px; min-height:44px; }
    .resource-tags { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px; }
    .tag { background: rgba(255,255,255,0.03); padding:6px 8px; border-radius:8px; font-size:12px; color:#cfe8ff; }
    .small-muted { color:#9fb8d9; font-size:13px; }
    .bookmark-btn { background:transparent; border:1px solid rgba(255,255,255,0.06); padding:6px 10px; border-radius:10px; color:#cfe8ff; }
    .search-row { display:flex; gap:10px; align-items:center; margin-bottom:12px; }

    /* Booking visuals (keep these so the colours show) */
    .slot-box { width:100%; height:56px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:700; }
    .slot-available { background: linear-gradient(180deg,#1e7f34,#166826); color:#fff; }
    .slot-unavailable { background: linear-gradient(180deg,#b02a2a,#8a1f1f); color:#fff; }
    .slot-lunch { background: linear-gradient(180deg,#3f4750,#2b3137); color:#e6eef8; opacity:0.95; }
    .legend { display:flex; gap:18px; align-items:center; margin-bottom:14px; }
    .legend .sw { width:18px; height:18px; border-radius:4px; display:inline-block; }
    .day-label { font-weight:700; color:#cfe8ff; width:110px; }
    
    @media (max-width:1000px){ .resource-grid { grid-template-columns: 1fr; } .cards-grid { grid-template-columns: 1fr; } }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------
# Booking & store setup (unchanged)
# -----------------------
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SLOTS = [
    "9 A.M. to 10 A.M.",
    "10 A.M. to 11 A.M.",
    "11 A.M. to 12 P.M.",
    "12 P.M. to 1 P.M.",
    "1 P.M. to 2 P.M.",  # lunch
    "2 P.M. to 3 P.M.",
    "3 P.M. to 4 P.M.",
    "4 P.M. to 5 P.M.",
    "5 P.M. to 6 P.M.",
]
LUNCH_SLOT_INDEX = SLOTS.index("1 P.M. to 2 P.M.")
today_idx = datetime.now().weekday()
RESET_WEEK_ON_SUNDAY = True


def make_token(n=8):
    alphabet = string.ascii_uppercase + string.digits + string.ascii_lowercase
    return "".join(secrets.choice(alphabet) for _ in range(n))


def key(d, s):
    return f"{d}_{s}"


def is_past_locked(d):
    if RESET_WEEK_ON_SUNDAY and today_idx == 6:
        return False
    return d < today_idx


# session UI state — add resources flag (no other changes)
if "show_chat" not in st.session_state:
    st.session_state.show_chat = False
if "show_booking" not in st.session_state:
    st.session_state.show_booking = False
if "show_resources" not in st.session_state:
    st.session_state.show_resources = False  # <--- new: resources toggle
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = set()
if "active_resource" not in st.session_state:
    st.session_state.active_resource = None

# load shared store (bookings/availability)
store = load_data()
store.setdefault("availability", {})
for d in range(7):
    for s in range(len(SLOTS)):
        if f"{d}_{s}" not in store["availability"]:
            if RESET_WEEK_ON_SUNDAY and today_idx == 6:
                store["availability"][f"{d}_{s}"] = True
            else:
                store["availability"][f"{d}_{s}"] = False if d < today_idx else True
save_data(store)

# -----------------------
# Resources: improved titles + descriptions (from your provided lists)
# -----------------------
RESOURCES = [
    {"id":"v1","title":"Study Tips: Beat Exam Stress","desc":"Short practical techniques to reduce exam anxiety and study more effectively.","tags":["study","stress","exams"],"type":"video","url":"https://youtu.be/Jk4WpJpjq7k?si=1uEEMycG3OLXiA3q"},
    {"id":"v2","title":"Active Revision Techniques","desc":"Learn active recall and spaced repetition tricks to boost retention.","tags":["study","revision"],"type":"video","url":"https://youtu.be/izJ3yhXPJ60?si=F2hVzpxUH9KTfWlp"},
    {"id":"v3","title":"Time Management for Students","desc":"How to plan study blocks, breaks and get more done with less stress.","tags":["productivity","planning"],"type":"video","url":"https://youtu.be/APS6t-auzM4?si=pXy-akR5jrefQgpk"},
    {"id":"v4","title":"Focus & Concentration Exercises","desc":"Short exercises to improve focus during study sessions.","tags":["focus","exercise"],"type":"video","url":"https://youtu.be/zklPS8qlW6c?si=p4Gjfmdh_gNm8TDp"},
    {"id":"ncert","title":"NCERT Resources","desc":"Official NCERT textbooks and resources (national curriculum materials).","tags":["ncert","textbook"],"type":"link","url":"https://ncert.nic.in/"},
    {"id":"v5","title":"Short Mindfulness Break (5 min)","desc":"A short guided grounding exercise to calm nerves and re-centre.","tags":["mindfulness","breathing"],"type":"video","url":"https://youtu.be/mdo19qOX-E4?si=LLcpUOqDGbOQsBbv"},
    {"id":"v6","title":"Guided Breathing for Stress","desc":"Simple breathing practice to reduce acute stress and nervousness.","tags":["breathing","relaxation"],"type":"video","url":"https://youtu.be/Nlz8yKG0ySU?si=d8He7OH82EC7ugvT"},
    {"id":"v7","title":"Quick Grounding Audio","desc":"A short grounding audio to use between study sessions.","tags":["audio","grounding"],"type":"video","url":"https://youtu.be/eAK14VoY7C0?si=35IjvElVRG-ID0mK"},
    {"id":"v8","title":"Study Break Movement","desc":"Two-minute movement routine to refresh posture and attention.","tags":["movement","wellbeing"],"type":"video","url":"https://youtu.be/deAIK86Hyxk?si=YBrcNiJP8ahMsvY8"},
    {"id":"v9","title":"Sleep & Memory Tips","desc":"Short tips to improve sleep quality for better learning and memory.","tags":["sleep","health"],"type":"video","url":"https://youtu.be/bPM-FDTuit8?si=14VV0WiujOV5cul0"},
    {"id":"v10","title":"7-minute Focus Practice","desc":"A short practice to build concentration and reduce distractibility.","tags":["focus","practice"],"type":"video","url":"https://youtu.be/iyY_LVKfOO0?si=YW8dfJtEwmLMdV1j"},
    {"id":"v11","title":"Calm Your Mind — Guided Short","desc":"Brief guided exercise to de-escalate anxious thoughts.","tags":["anxiety","calm"],"type":"video","url":"https://youtu.be/hzvT0vy5cjE?si=YeFeCEkoI0LDb2bn"},
    {"id":"v12","title":"Study Motivation & Habits","desc":"How to form small habits that keep motivation steady over time.","tags":["motivation","habits"],"type":"video","url":"https://youtu.be/N6NlJgSf7r0?si=cuFk13rIaLy3mWY6"},
    {"id":"v13","title":"Active Note-taking Strategies","desc":"Effective note patterns to make reviewing faster and clearer.","tags":["notes","study"],"type":"video","url":"https://youtu.be/RJHZ01TzY9M?si=NMPskFPf8NT1vHdx"},
    {"id":"v14","title":"Stress-to-Action: Small Steps","desc":"How to convert stress into small practical steps you can take now.","tags":["stress","action"],"type":"video","url":"https://youtu.be/7NLfpsNHmZI?si=zCBGbc4h9AHg4bX8"},
    {"id":"gm1","title":"Guided Meditation — Self-Love","desc":"A gentle guided meditation to build self-compassion and calm.","tags":["meditation","self-love"],"type":"video","url":"https://youtu.be/vj0JDwQLof4?si=-3AI1c7f60JKhcSn"},
    {"id":"gm2","title":"Guided Relaxation — Body Scan","desc":"A short body scan meditation to relieve tension and stress.","tags":["meditation","relaxation"],"type":"video","url":"https://youtu.be/sfSDQRdIvTc?si=JAWlk4la8ZtV0D-K"},
    {"id":"gm3","title":"Breathing & Grounding Session","desc":"Breath-led grounding practice for quick resets during the day.","tags":["meditation","breathing"],"type":"video","url":"https://youtu.be/uNmKzlh55Fo?si=fPV3KbDffre6ttBn"},
    {"id":"gm4","title":"Short Guided Calm (video)","desc":"A concise calm practice for pre-sleep or study breaks.","tags":["meditation","calm"],"type":"video","url":"https://youtu.be/C4bofW53sO8?si=yinXXWC4CqahOwDx"},
    {"id":"gm5","title":"Self-care Meditation (7 min)","desc":"Self-care focused practice to improve mood and perspective.","tags":["meditation","self-care"],"type":"video","url":"https://youtu.be/blbv5UTBCGg?si=W0W6QYtILD6kNMUl"},
    {"id":"mi1","title":"Mindset: Controlling Thoughts 1","desc":"Techniques for noticing and gently redirecting unhelpful thoughts.","tags":["mindset","thoughts"],"type":"video","url":"https://youtu.be/22wpwgpy7fY?si=ZbUXEGNZeD7p0gl5"},
    {"id":"mi2","title":"Cognitive Strategies for Focus","desc":"How to shift thinking patterns that distract from study.","tags":["mindset","focus"],"type":"video","url":"https://youtu.be/U_ilabJbPKU?si=IvpT9vNE9G6vEHZA"},
    {"id":"mi3","title":"Thought Reframing Basics","desc":"Short guide to reframing negative thoughts into neutral steps.","tags":["reframing","cbt"],"type":"video","url":"https://youtu.be/nqxviz_G4Uo?si=KLfVRcmmQxIK_eD8"},
    {"id":"mi4","title":"Sustaining Attention Techniques","desc":"Practical steps to keep attention from wandering during work.","tags":["attention","techniques"],"type":"video","url":"https://youtu.be/KzW84p4bCzA?si=stKdsbcfW81c9-TF"},
    {"id":"mi5","title":"Managing Overthinking","desc":"Short methods to interrupt overthinking cycles and ground yourself.","tags":["overthinking","mindset"],"type":"video","url":"https://youtu.be/nnSRJ5PRPWQ?si=W20BQjBabnR80pqX"},
    {"id":"pod1","title":"Mental Health Podcast — Ep.1","desc":"A thoughtful conversation about coping with stress and study life.","tags":["podcast","mental-health"],"type":"video","url":"https://youtu.be/MFyEwdpC5pM?si=Ts-jLPxH5FvnaaAP"},
    {"id":"pod2","title":"Mental Health Podcast — Ep.2","desc":"Stories, tips and small steps from mental health practitioners.","tags":["podcast","support"],"type":"video","url":"https://youtu.be/9EqrUK7ghho?si=ydVsJeRZFjsqQVS-"},
    {"id":"pod3","title":"Mental Health Podcast — Tools","desc":"Practical tools for everyday wellbeing and stress management.","tags":["podcast","tools"],"type":"video","url":"https://youtu.be/Kqya9ql7hM0?si=DKuKPTpQzOO3-ytj"},
    {"id":"pod4","title":"Mental Health Podcast — Study Life","desc":"Advice for students balancing study and wellbeing.","tags":["podcast","students"],"type":"video","url":"https://youtu.be/YcGXViwXItM?si=mhATIev5NxG-XHlC"},
    {"id":"pod5","title":"Mental Health Podcast — Self-care","desc":"Episode focused on self-care routines that actually work.","tags":["podcast","self-care"],"type":"video","url":"https://youtu.be/YWBuwJTuWGo?si=FFfthEyOYEa4N8Vs"},
]

# -----------------------
# Resources hub UI (rendered at bottom of homepage only when requested)
# -----------------------
def render_resource_card(r):
    """Render a single resource as a card. 'Open / Download' sets active_resource for inline viewer."""
    st.markdown("<div class='resource-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='resource-title'>{r['title']}</div>", unsafe_allow_html=True)
    desc = r.get("desc", "")
    if desc:
        st.markdown(f"<div class='resource-desc'>{desc}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='resource-desc'>&nbsp;</div>", unsafe_allow_html=True)

    # tags
    tag_html = "<div class='resource-tags'>"
    for t in r["tags"]:
        tag_html += f"<div class='tag'>{t}</div>"
    tag_html += "</div>"
    st.markdown(tag_html, unsafe_allow_html=True)

    # action row
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Open / Download", key=f"open_{r['id']}"):
            # set active resource to show viewer below (Streamlit will rerun on button click)
            st.session_state.active_resource = r["id"]
    with col2:
        if r["id"] in st.session_state.bookmarks:
            if st.button("Bookmarked ✓", key=f"bm_on_{r['id']}"):
                # unbookmark (no explicit rerun call required)
                st.session_state.bookmarks.remove(r["id"])
                st.success("Removed from bookmarks")
        else:
            if st.button("Save", key=f"bm_off_{r['id']}"):
                st.session_state.bookmarks.add(r["id"])
                st.success("Saved to bookmarks")

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------
# Fullscreen chat (unchanged)
# -----------------------
if st.session_state.show_chat:
    topcols = st.columns([8, 1])
    with topcols[0]:
        st.markdown("<h1>Heal Nest — Chat (Full screen)</h1>", unsafe_allow_html=True)
    with topcols[1]:
        if st.button("Close Chatbot"):
            st.session_state.show_chat = False
            st.rerun()
    botpress_url = "https://cdn.botpress.cloud/webchat/v3.2/shareable.html?configUrl=https://files.bpcontent.cloud/2025/09/13/22/20250913220458-U8RB73H5.json"
    components.html(
        f"""
        <style>html,body,iframe{{height:100%; margin:0}}</style>
        <iframe src="{botpress_url}" style="position:fixed; top:60px; left:0; width:100%; height:calc(100% - 60px); border:0;" allow="microphone; camera;"></iframe>
    """,
        height=900,
    )
    st.stop()

# -----------------------
# Fullscreen booking (unchanged)
# -----------------------
if st.session_state.show_booking:
    cols = st.columns([8, 1])
    with cols[0]:
        st.markdown("<h1>Book Counsellor — Weekly Availability</h1>", unsafe_allow_html=True)
    with cols[1]:
        if st.button("Close Booking"):
            st.session_state.show_booking = False
            st.rerun()
    st.markdown("---")
    st.markdown(
        """<div class='legend'><div class='item'><span class='sw' style='background:#1e7f34'></span><span class='label'>Available</span></div>
                   <div class='item'><span class='sw' style='background:#b02a2a'></span><span class='label'>Booked / Unavailable</span></div>
                   <div class='item'><span class='sw' style='background:#3f4750'></span><span class='label'>Lunch / Disabled</span></div></div>""",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # header
    header_cols = st.columns([1.1] + [1 for _ in SLOTS])
    header_cols[0].markdown("<strong>Day / Time</strong>", unsafe_allow_html=True)
    for i, s in enumerate(SLOTS):
        header_cols[i + 1].markdown(
            f"<div style='text-align:center;font-weight:700;color:#cfe8ff'>{s}</div>", unsafe_allow_html=True
        )

    for d_idx, day in enumerate(DAYS):
        row_cols = st.columns([1.1] + [1 for _ in SLOTS])
        row_cols[0].markdown(f"<div class='day-label'>{day}</div>", unsafe_allow_html=True)
        for s_idx, slot_label in enumerate(SLOTS):
            locked = is_past_locked(d_idx)
            is_lunch = s_idx == LUNCH_SLOT_INDEX
            avail = store["availability"].get(key(d_idx, s_idx), True)

            if locked:
                avail = False
                store["availability"][key(d_idx, s_idx)] = False

            if is_lunch:
                row_cols[s_idx + 1].markdown("<div class='slot-box slot-lunch'>Lunch</div>", unsafe_allow_html=True)
            else:
                if avail:
                    row_cols[s_idx + 1].markdown("<div class='slot-box slot-available'>Available</div>", unsafe_allow_html=True)
                    btn_key = f"book_{d_idx}_{s_idx}"
                    if row_cols[s_idx+1].button("Book", key=btn_key):
                        if locked:
                            st.warning("This day's slots are locked (past day). Booking not allowed.")
                        else:
                            token = make_token(8)
                            timestamp_iso = datetime.now().isoformat()
                            store["availability"][key(d_idx, s_idx)] = False
                            store.setdefault("bookings", []).append(
                                {"day": d_idx, "slot": s_idx, "token": token, "time": timestamp_iso}
                            )
                            save_data(store)
                            st.success(f"Booked {day} — {slot_label}. Your token: {token}")
                            st.rerun()
                else:
                    row_cols[s_idx + 1].markdown("<div class='slot-box slot-unavailable'>Booked / Unavailable</div>", unsafe_allow_html=True)
                    btn_key = f"cancel_{d_idx}_{s_idx}"
                    if row_cols[s_idx+1].button("Cancel", key=btn_key):
                        if locked:
                            st.warning("Cannot change past-day slots — locked until weekly reset.")
                        else:
                            store["availability"][key(d_idx, s_idx)] = True
                            for i, b in enumerate(store.get("bookings", [])):
                                if b["day"] == d_idx and b["slot"] == s_idx:
                                    store["bookings"].pop(i)
                                    break
                            save_data(store)
                            st.info(f"Cancelled booking for {day} — {slot_label}")
                            st.rerun()

    save_data(store)
    st.markdown("---")
    st.caption("Note: booking token is the only identifier. Keep it to manage or verify your booking.")
    st.stop()

# -----------------------
# Homepage (with Resources Hub trigger)
# -----------------------
# Display logo (left) + title (right) — no upload option, uses local paths fallback
LOGO_CANDIDATES = [
    r"healnest.png",
    "logo.png",
    "logo.jpg",
]

logo_path = None
for p in LOGO_CANDIDATES:
    try:
        if os.path.exists(p):
            logo_path = p
            break
    except Exception:
        continue

if logo_path:
    c1, c2 = st.columns([1, 8])
    with c1:
        try:
            st.image(logo_path, width=140)
        except Exception:
            pass
    with c2:
        st.title("Heal Nest — Student Support Chatbot (Prototype)")
        st.markdown("*Prototype UI — not a replacement for professional help.*")
else:
    st.title("Heal Nest — Student Support Chatbot (Prototype)")
    st.markdown("*Prototype UI — not a replacement for professional help.*")

st.markdown("---")

# main cards
st.markdown('<div class="cards-grid">', unsafe_allow_html=True)
st.markdown("<div class='ms-card'><h2>Talk to Chatbot</h2><p>Confidential, empathetic chat powered by embedded Botpress.</p></div>", unsafe_allow_html=True)
if st.button("Open Chatbot"):
    st.session_state.show_chat = True
    st.rerun()

st.markdown("<div class='ms-card'><h2>Peer Support Forum</h2><p>Connect anonymously with fellow students.</p></div>", unsafe_allow_html=True)
if st.button("Open Forum (placeholder)"):
    st.info("Forum UI placeholder")

st.markdown("<div class='ms-card'><h2>Book Counsellor</h2><p>Schedule a confidential session with campus counselling services.</p></div>", unsafe_allow_html=True)
if st.button("Book Counsellor"):
    st.session_state.show_booking = True
    st.rerun()

st.markdown("<div class='ms-card'><h2>Resources Hub</h2><p>Guides, helplines, and short exercises for wellbeing and study skills.</p></div>", unsafe_allow_html=True)
if st.button("Browse Resources"):
    # show resources area (bottom of the homepage)
    st.session_state.show_resources = True
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('---')

# -----------------------
# Resources Hub (rendered at bottom of homepage only when requested)
# -----------------------
if st.session_state.show_resources:
    st.subheader("Resources Hub — curated materials for students")
    st.markdown("Search, filter, and save resources to your bookmarks. Everything is anonymous.")

    # search + filters row
    q_col, tag_col, view_col = st.columns([5, 3, 2])
    query = q_col.text_input("Search resources", placeholder="Search titles, descriptions, tags...")
    tag_options = sorted({t for r in RESOURCES for t in r["tags"]})
    selected_tags = tag_col.multiselect("Filter tags", tag_options)
    view_choice = view_col.radio("View", ["All", "Bookmarked"], index=0)

    # build filtered list
    def matches(r):
        if view_choice == "Bookmarked" and r["id"] not in st.session_state.bookmarks:
            return False
        if selected_tags and not set(selected_tags).issubset(set(r["tags"])):
            return False
        if query:
            q = query.lower()
            if q not in r["title"].lower() and q not in r["desc"].lower() and not any(q in t for t in r["tags"]):
                return False
        return True

    filtered = [r for r in RESOURCES if matches(r)]

    st.markdown(f"**{len(filtered)}** resource(s) — showing { 'bookmarked' if view_choice=='Bookmarked' else 'all' } results")
    st.markdown("---")

    # render grid
    if not filtered:
        st.info("No resources match your search/filters.")
    else:
        cols = st.columns(3)
        for i, r in enumerate(filtered):
            with cols[i % 3]:
                render_resource_card(r)

    st.markdown("---")

    # Inline viewer for active resource
    if st.session_state.active_resource:
        ar_id = st.session_state.active_resource
        ar = next((x for x in RESOURCES if x["id"] == ar_id), None)
        if ar:
            st.markdown("### Opened resource")
            st.markdown(f"**{ar['title']}**")
            if ar["type"] == "video":
                # st.video accepts full YouTube URLs
                try:
                    st.video(ar["url"])
                except Exception:
                    st.write("Unable to render video inline — open link below:")
                    st.markdown(f"[Open resource]({ar['url']})")
            else:
                st.markdown(f"[Open resource]({ar['url']})")
            if st.button("Close resource"):
                st.session_state.active_resource = None

    st.markdown("---")
    st.subheader("My Bookmarks")
    if not st.session_state.bookmarks:
        st.write("You have no bookmarks yet — save resources to find them here.")
    else:
        # show bookmarked items
        for rid in list(st.session_state.bookmarks):
            r = next((x for x in RESOURCES if x["id"] == rid), None)
            if r:
                with st.expander(r["title"]):
                    st.write(r["desc"])
                    st.write("Tags:", ", ".join(r["tags"]))
                    if st.button("Remove bookmark", key=f"unbm_{rid}"):
                        st.session_state.bookmarks.remove(rid)
                        st.success("Removed bookmark")

    st.markdown("---")
    if st.button("Close Resources Hub"):
        st.session_state.show_resources = False
        st.session_state.active_resource = None
        st.rerun()

# -----------------------
# Footer / Contact (unchanged)
# -----------------------
st.markdown('---')
col1, col2 = st.columns([3, 1])
with col1:
    st.header("Contact & Support")
    st.write("For demos: demo@healnest.edu")
    st.write("Campus counselling: +91-XXXXXXXXXX")
with col2:
    st.write("")
    st.write("\u00A9 2025 Heal Nest — Demo")

st.markdown('---')
st.caption("If you or someone is in immediate danger, contact local emergency services immediately.")

