import streamlit as st
from utils.queries import (
    add_event_field, delete_event_field,
    add_registration_field, delete_registration_field,
    get_event_fields, get_registration_fields,
)

FIELD_TYPES  = ["text", "number", "date", "dropdown"]
FIELD_ICONS  = {"text": "✏️", "number": "🔢", "date": "📅", "dropdown": "🔽"}


# ── DYNAMIC EVENT FIELD BUILDER (used in Create/Edit Event) ─────────────────

def render_event_field_builder(event_id: int | None = None, key_prefix: str = "ef"):
    """
    If event_id is None  → temp fields stored in session_state (create mode)
    If event_id is set   → fields saved to DB immediately (edit mode)
    """
    ss_key = f"{key_prefix}_fields"
    if ss_key not in st.session_state:
        if event_id:
            st.session_state[ss_key] = get_event_fields(event_id)
        else:
            st.session_state[ss_key] = []

    st.markdown("""
    <div class="form-section-title">📋 Event Info Fields
        <span style="font-weight:400;color:var(--text-muted);font-size:0.7rem;
                     text-transform:none;letter-spacing:0;">
            — custom fields displayed on the event page
        </span>
    </div>""", unsafe_allow_html=True)

    # Existing fields
    fields = st.session_state[ss_key]
    for i, f in enumerate(fields):
        c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
        with c1:
            st.text_input("Name", value=f["field_name"], key=f"{key_prefix}_fn_{i}", disabled=bool(event_id))
        with c2:
            st.selectbox("Type", FIELD_TYPES, index=FIELD_TYPES.index(f["field_type"]),
                         key=f"{key_prefix}_ft_{i}", disabled=bool(event_id))
        with c3:
            st.text_input("Value", value=f.get("field_value",""), key=f"{key_prefix}_fv_{i}", disabled=bool(event_id))
        with c4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑", key=f"{key_prefix}_fdel_{i}", help="Remove field"):
                if event_id and f.get("id"):
                    delete_event_field(f["id"])
                st.session_state[ss_key].pop(i)
                st.rerun()

    # Add new field row
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container():
        c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
        with c1:
            new_name = st.text_input("Field Name", key=f"{key_prefix}_new_name", placeholder="e.g. Speaker")
        with c2:
            new_type = st.selectbox("Type", FIELD_TYPES, key=f"{key_prefix}_new_type")
        with c3:
            new_val  = st.text_input("Value", key=f"{key_prefix}_new_val", placeholder="e.g. Dr. Smith")
        with c4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Add", key=f"{key_prefix}_add_btn"):
                if new_name.strip():
                    entry = {"field_name": new_name.strip(), "field_type": new_type, "field_value": new_val}
                    if event_id:
                        fid = add_event_field(event_id, new_name.strip(), new_type, new_val)
                        entry["id"] = fid
                    st.session_state[ss_key].append(entry)
                    st.rerun()
                else:
                    st.warning("Field name required.")

    return st.session_state[ss_key]


# ── DYNAMIC REGISTRATION FIELD BUILDER ──────────────────────────────────────

def render_registration_field_builder(event_id: int | None = None, key_prefix: str = "rf"):
    ss_key = f"{key_prefix}_reg_fields"
    if ss_key not in st.session_state:
        if event_id:
            st.session_state[ss_key] = get_registration_fields(event_id)
        else:
            st.session_state[ss_key] = []

    st.markdown("""
    <div class="form-section-title">📝 Registration Form Fields
        <span style="font-weight:400;color:var(--text-muted);font-size:0.7rem;
                     text-transform:none;letter-spacing:0;">
            — what students fill in when registering
        </span>
    </div>""", unsafe_allow_html=True)

    fields = st.session_state[ss_key]
    for i, f in enumerate(fields):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 1, 3, 1])
        with c1:
            st.text_input("Label", value=f["field_name"], key=f"{key_prefix}_rfn_{i}", disabled=bool(event_id))
        with c2:
            st.selectbox("Type", FIELD_TYPES, index=FIELD_TYPES.index(f["field_type"]),
                         key=f"{key_prefix}_rft_{i}", disabled=bool(event_id))
        with c3:
            st.checkbox("Req", value=bool(f.get("is_required", 1)),
                        key=f"{key_prefix}_rfr_{i}", disabled=bool(event_id))
        with c4:
            opts = f.get("options", "") or ""
            st.text_input("Options (comma-sep)", value=opts,
                          key=f"{key_prefix}_rfo_{i}", placeholder="Opt1, Opt2",
                          disabled=bool(event_id) or f["field_type"] != "dropdown")
        with c5:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑", key=f"{key_prefix}_rfdel_{i}", help="Remove"):
                if event_id and f.get("id"):
                    delete_registration_field(f["id"])
                st.session_state[ss_key].pop(i)
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([3, 2, 1, 3, 1])
    with c1:
        rn_name = st.text_input("Label", key=f"{key_prefix}_rn_name", placeholder="e.g. Phone")
    with c2:
        rn_type = st.selectbox("Type", FIELD_TYPES, key=f"{key_prefix}_rn_type")
    with c3:
        rn_req  = st.checkbox("Req", value=True, key=f"{key_prefix}_rn_req")
    with c4:
        rn_opts = st.text_input("Options", key=f"{key_prefix}_rn_opts",
                                placeholder="Only for dropdown",
                                disabled=(rn_type != "dropdown"))
    with c5:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Add", key=f"{key_prefix}_radd"):
            if rn_name.strip():
                entry = {
                    "field_name":  rn_name.strip(),
                    "field_type":  rn_type,
                    "is_required": int(rn_req),
                    "options":     rn_opts if rn_type == "dropdown" else "",
                }
                if event_id:
                    fid = add_registration_field(
                        event_id, rn_name.strip(), rn_type, rn_req,
                        rn_opts if rn_type == "dropdown" else ""
                    )
                    entry["id"] = fid
                st.session_state[ss_key].append(entry)
                st.rerun()
            else:
                st.warning("Field label required.")

    return st.session_state[ss_key]


# ── CSV DOWNLOAD BUTTON ───────────────────────────────────────────────────────
def csv_download_button(df, filename: str = "export.csv", label: str = "⬇️ Download CSV"):
    if df.empty:
        st.info("No data to export.")
        return
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label, data=csv, file_name=filename, mime="text/csv")
