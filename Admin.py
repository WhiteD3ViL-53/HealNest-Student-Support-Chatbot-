# Admin.py — Heal Nest Admin / Counsellor Dashboard (tokens-only, safe rerun)
# Save to: C:\Users\SIDDHANT THAKUR\Desktop\weatherapp\Admin.py

import io
import csv
import os
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

# local helper to persist data (must be present in same folder)
from data_store_utils import load_data, save_data

# load .env if present (for ADMIN_PASSWORD)
load_dotenv()

# -----------------------
# Page config & styles
# -----------------------
st.set_page_config(page_title="Heal Nest — Admin Dashboard", layout="wide")

st.markdown(
    """
    <style>
    :root{--bg:#081026;--card:#0b1220;--muted:#cfe8ff}
    body { background-color: var(--bg); color: #e6eef8; }
    .admin-wrap { max-width:1300px; margin:8px auto; }
    .admin-panel { background: linear-gradient(180deg, rgba(11,18,32,0.95), rgba(6,10,18,0.95)); padding:18px; border-radius:12px; box-shadow:0 10px 30px rgba(0,0,0,0.5); }
    .slot-box { width:100%; height:48px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:700; }
    .slot-available { background: linear-gradient(180deg,#1e7f34,#166826); color:#fff; }
    .slot-unavailable { background: linear-gradient(180deg,#b02a2a,#8a1f1f); color:#fff; }
    .slot-lunch { background: linear-gradient(180deg,#3f4750,#2b3137); color:#e6eef8; opacity:0.95; }
    .legend { display:flex; gap:18px; align-items:center; margin-bottom:14px; }
    .legend .sw { width:18px; height:18px; border-radius:4px; display:inline-block; }
    .day-label { font-weight:700; color:#cfe8ff; width:110px; }
    .stButton>button { border-radius:10px; padding:8px 12px; font-weight:600; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------
# Show Logo
# -----------------------
LOGO_PATH = r"healnest.png"
if os.path.exists(LOGO_PATH):
    try:
        st.image(LOGO_PATH, width=160)
    except Exception as e:
        st.warning(f"Could not load logo: {e}")
else:
    st.info(f"Logo not found at {LOGO_PATH}")

# -----------------------
# Helpers
# -----------------------
def safe_rerun():
    """Try to call Streamlit's rerun. If not available, force a browser reload via JS."""
    try:
        st.experimental_rerun()
    except Exception:
        # fallback to reload via JS
        components.html("<script>window.location.reload()</script>")
        st.stop()


# -----------------------
# Load shared data store
# -----------------------
store = load_data()
store.setdefault("availability", {})
store.setdefault("bookings", [])
store.setdefault("counsellors", [])
store.setdefault("chat_logs", [])

# -----------------------
# Constants
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
try:
    LUNCH_SLOT_INDEX = SLOTS.index("1 P.M. to 2 P.M.")
except ValueError:
    LUNCH_SLOT_INDEX = 4

today_idx = datetime.now().weekday()  # Mon=0..Sun=6
RESET_WEEK_ON_SUNDAY = True

# -----------------------
# Admin password
# -----------------------
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "adminpass")

# -----------------------
# Sidebar login
# -----------------------
st.sidebar.title("Admin Login")
pw = st.sidebar.text_input("Enter admin password", type="password")
if not pw:
    st.sidebar.info("Enter password to continue.")
    st.stop()
if pw != ADMIN_PASSWORD:
    st.sidebar.error("Incorrect password.")
    st.stop()

# -----------------------
# Admin UI
# -----------------------
st.markdown('<div class="admin-wrap">', unsafe_allow_html=True)
st.header("Heal Nest — Admin / Counsellor Dashboard")
st.markdown("<div class='admin-panel'>", unsafe_allow_html=True)

tabs = st.tabs(["Overview", "Bookings", "Availability", "Counsellors", "Chat Logs", "Reports"])


def persist():
    save_data(store)


# --- Overview ---
with tabs[0]:
    st.subheader("Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total bookings", str(len(store.get("bookings", []))))
    upcoming = [b for b in store.get("bookings", []) if b.get("day", -1) >= today_idx]
    c2.metric("This week", str(len(upcoming)))
    c3.metric("Counsellors", str(len(store.get("counsellors", []))))

    st.markdown("---")
    st.subheader("Quick actions")
    qa1, qa2, qa3 = st.columns(3)
    if qa1.button("Reset week (make all slots available)"):
        for d in range(7):
            for s in range(len(SLOTS)):
                store["availability"][f"{d}_{s}"] = True
        persist()
        st.success("Week reset — all slots available.")
    if qa2.button("Lock past days (apply rules)"):
        for d in range(7):
            for s in range(len(SLOTS)):
                if RESET_WEEK_ON_SUNDAY and today_idx == 6:
                    continue
                if d < today_idx:
                    store["availability"][f"{d}_{s}"] = False
        persist()
        st.success("Applied past-day locking rules.")
    if qa3.button("Clear all bookings"):
        store["bookings"] = []
        persist()
        st.success("All bookings cleared.")


# --- Bookings (tokens-only; no admin create UI) ---
with tabs[1]:
    st.subheader("Bookings")
    st.markdown("**Note:** Bookings are anonymous — only token and timestamp are stored.")
    st.markdown("---")

    if not store.get("bookings"):
        st.info("No bookings yet.")
    else:
        for idx, b in enumerate(list(store["bookings"])): 
            day_str = DAYS[b.get("day", -1)] if "day" in b else "-"
            slot_str = SLOTS[b.get("slot", -1)] if "slot" in b else "-"
            with st.expander(f"{idx+1}. {day_str} — {slot_str}"):
                st.write(f"**Token:** {b.get('token', '-')}")
                st.write(f"**Time:** {b.get('time', '-')}")
                if st.button(f"Remove booking #{idx+1}", key=f"remove_{idx}"):
                    try:
                        store["availability"][f"{b['day']}_{b['slot']}"] = True
                    except Exception:
                        pass
                    store["bookings"].pop(idx)
                    persist()
                    st.success("Booking removed.")
                    safe_rerun()


# --- Availability ---
with tabs[2]:
    st.subheader("Manage Availability")
    st.markdown("Legend: green = available, red = unavailable, grey = lunch")
    st.markdown("---")
    for d_idx, day in enumerate(DAYS):
        cols = st.columns([1.2] + [1 for _ in SLOTS])
        cols[0].markdown(f"**{day}**")
        for s_idx, slot_label in enumerate(SLOTS):
            is_lunch = (s_idx == LUNCH_SLOT_INDEX)
            avail = store.get("availability", {}).get(f"{d_idx}_{s_idx}", True)
            if is_lunch:
                cols[s_idx + 1].markdown("<div class='slot-box slot-lunch'>Lunch</div>", unsafe_allow_html=True)
            else:
                if avail:
                    cols[s_idx + 1].markdown("<div class='slot-box slot-available'>Available</div>", unsafe_allow_html=True)
                    if cols[s_idx + 1].button(f"Set Unavailable_{d_idx}_{s_idx}", key=f"un_{d_idx}_{s_idx}"):
                        store["availability"][f"{d_idx}_{s_idx}"] = False
                        persist()
                        st.success("Slot set unavailable")
                        safe_rerun()
                else:
                    cols[s_idx + 1].markdown("<div class='slot-box slot-unavailable'>Unavailable</div>", unsafe_allow_html=True)
                    if cols[s_idx + 1].button(f"Set Available_{d_idx}_{s_idx}", key=f"av_{d_idx}_{s_idx}"):
                        store["availability"][f"{d_idx}_{s_idx}"] = True
                        persist()
                        st.success("Slot set available")
                        safe_rerun()


# --- Counsellors ---
with tabs[3]:
    st.subheader("Counsellors")
    if not store.get("counsellors"):
        st.info("No counsellors configured.")
    else:
        for c in list(store["counsellors"]):
            cols = st.columns([4, 1])
            cols[0].markdown(f"**{c['id']}. {c['name']}** — {c['specialty']}")
            if cols[1].button(f"Remove_{c['id']}", key=f"remc_{c['id']}"):
                store["counsellors"] = [x for x in store["counsellors"] if x["id"] != c["id"]]
                persist()
                st.success("Counsellor removed")
                safe_rerun()
    st.markdown("---")
    st.subheader("Add counsellor")
    nc_name = st.text_input("Name", key="nc_name")
    nc_spec = st.text_input("Specialty", key="nc_spec")
    if st.button("Add counsellor"):
        nid = max([c["id"] for c in store.get("counsellors", [])] + [0]) + 1
        store.setdefault("counsellors", []).append({"id": nid, "name": nc_name or f"Counsellor {nid}", "specialty": nc_spec or "General"})
        persist()
        st.success("Counsellor added")
        safe_rerun()


# --- Chat logs ---
with tabs[4]:
    st.subheader("Chat Logs (placeholder)")
    if not store.get("chat_logs"):
        st.info("No chat logs recorded in demo mode.")
    else:
        for log in store.get("chat_logs", []):
            st.markdown(f"**{log.get('user','User')}** — {log.get('time','-')}")
            st.write(log.get("text", ""))


# --- Reports ---
with tabs[5]:
    st.subheader("Reports")
    if st.button("Export bookings CSV"):
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["day", "slot", "token", "timestamp"])
        for b in store.get("bookings", []):
            writer.writerow([DAYS[b["day"]], SLOTS[b["slot"]], b.get("token", ""), b.get("time", "")])
        st.download_button("Download bookings.csv", data=buf.getvalue(), file_name="bookings.csv", mime="text/csv")
print("[Admin.py] module loaded")


st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
st.caption("Heal Nest admin dashboard — protected by password. Data stored in data_store.json.")


