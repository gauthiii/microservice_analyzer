import html
import json
import os
import platform
import subprocess
from pathlib import Path

import streamlit as st
from anthropic import Anthropic
from openai import OpenAI


st.set_page_config(
    page_title="AI Codebase Visualizer & Analyzer",
    page_icon="✨",
    layout="wide",
)

st.markdown(
    """
<style>
    :root {
        --app-bg: #080b12;
        --app-bg-soft: #0d111c;
        --panel: #111827;
        --panel-soft: #151f31;
        --sidebar: #0b1020;
        --field: #0f172a;
        --ink: #f8fafc;
        --muted: #94a3b8;
        --line: #253149;
        --line-strong: #334155;
        --accent: #38bdf8;
        --accent-dark: #0284c7;
        --accent-soft: rgba(56, 189, 248, 0.14);
        --tag-bg: #182235;
        --tag-border: #334155;
        --tag-text: #cbd5e1;
        --success: #22c55e;
        --shadow: 0 20px 48px rgba(0, 0, 0, 0.32);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(56, 189, 248, 0.12), transparent 28rem),
            linear-gradient(180deg, var(--app-bg-soft) 0%, var(--app-bg) 52%, #06080d 100%);
        color: var(--ink);
    }

    [data-testid="stHeader"] {
        background: rgba(8, 11, 18, 0.82);
        backdrop-filter: blur(10px);
    }

    [data-testid="stSidebar"] {
        background: var(--sidebar);
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] * {
        color: var(--ink) !important;
    }

    .block-container {
        padding-top: 2.25rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    h1, h2, h3 {
        color: var(--ink);
        letter-spacing: 0;
    }

    div[data-testid="stTextInput"] label,
    div[data-testid="stSelectbox"] label {
        color: var(--ink);
        font-weight: 700;
    }

    div[data-baseweb="input"],
    div[data-baseweb="select"] > div {
        background: var(--field) !important;
        border: 1px solid var(--line-strong) !important;
        border-radius: 10px !important;
        box-shadow: none !important;
    }

    div[data-testid="stTextInput"] input {
        background: var(--field) !important;
        color: var(--ink) !important;
        border: 0 !important;
        border-radius: 10px !important;
        min-height: 46px;
        box-shadow: none !important;
    }

    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.16) !important;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: #64748b !important;
        opacity: 1 !important;
    }

    div[data-baseweb="input"] button,
    div[data-baseweb="input"] button:hover,
    div[data-baseweb="input"] button:focus {
        background: transparent !important;
        border: 0 !important;
        box-shadow: none !important;
        color: var(--muted) !important;
        transform: none !important;
    }

    div[data-baseweb="select"] span,
    div[data-baseweb="select"] svg {
        color: var(--ink) !important;
        fill: var(--ink) !important;
    }

    div[data-testid="stButton"] button {
        border-radius: 10px;
        border: 1px solid var(--line-strong) !important;
        background: var(--panel-soft) !important;
        color: var(--ink) !important;
        min-height: 46px;
        font-weight: 750;
        transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;
    }

    div[data-testid="stButton"] button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        transform: translateY(-1px);
        box-shadow: 0 10px 24px rgba(56, 189, 248, 0.12);
    }

    div[data-testid="stButton"] button[kind="primary"] {
        background: var(--accent) !important;
        border-color: var(--accent) !important;
        color: #06101f !important;
    }

    div[data-testid="stButton"] button[kind="primary"]:hover {
        background: var(--accent-dark) !important;
        border-color: var(--accent-dark) !important;
        color: #ffffff !important;
    }

    .workbench-shell {
        border: 1px solid var(--line);
        border-radius: 18px;
        background: rgba(17, 24, 39, 0.86);
        box-shadow: var(--shadow);
        padding: 1.25rem;
        margin-bottom: 1rem;
    }

    .app-kicker {
        color: var(--accent);
        font-size: 0.76rem;
        font-weight: 850;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
    }

    .app-title {
        color: var(--ink);
        font-size: clamp(2rem, 4vw, 3.4rem);
        font-weight: 900;
        line-height: 1.02;
        letter-spacing: 0;
        margin: 0;
    }

    .app-subtitle {
        color: var(--muted);
        font-size: 1rem;
        max-width: 820px;
        margin: 0.75rem 0 0;
    }

    .section-card {
        border: 1px solid var(--line);
        border-radius: 16px;
        background: var(--panel);
        box-shadow: 0 14px 34px rgba(31, 41, 55, 0.06);
        padding: 1rem;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--line) !important;
        border-radius: 16px !important;
        background: var(--panel) !important;
        box-shadow: 0 14px 34px rgba(0, 0, 0, 0.22);
    }

    div[data-testid="stButton"] button p {
        color: inherit !important;
    }

    .panel-title {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        color: var(--ink);
        font-size: 1.05rem;
        font-weight: 850;
        margin: 0 0 0.85rem;
    }

    .panel-title-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        border-radius: 9px;
        background: var(--accent-soft);
        color: var(--accent-dark);
    }

    .skip-bar {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.45rem;
        color: var(--muted);
        font-size: 0.86rem;
        margin: 0.2rem 0 1.1rem;
    }

    .skip-label {
        color: var(--ink);
        font-weight: 800;
        margin-right: 0.2rem;
    }

    .skip-chip {
        display: inline-flex;
        align-items: center;
        border: 1px solid var(--tag-border);
        background: var(--tag-bg);
        color: var(--tag-text);
        border-radius: 999px;
        padding: 0.18rem 0.58rem;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.78rem;
        font-weight: 750;
    }

    .tree-shell {
        overflow: auto;
        max-height: 72vh;
        border: 1px solid var(--line);
        border-radius: 14px;
        background:
            linear-gradient(90deg, rgba(56, 189, 248, 0.07) 0, transparent 9rem),
            var(--panel);
    }

    .tree-root {
        position: sticky;
        top: 0;
        z-index: 1;
        display: flex;
        align-items: center;
        gap: 0.65rem;
        padding: 0.85rem 1rem;
        border-bottom: 1px solid var(--line);
        background: rgba(17, 24, 39, 0.94);
        backdrop-filter: blur(8px);
        color: var(--ink);
        font-weight: 900;
    }

    .root-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 10px;
        background: var(--accent);
        color: #ffffff;
        font-size: 0.9rem;
    }

    .tree-list {
        list-style: none;
        margin: 0;
        padding: 0.55rem 0.65rem 0.85rem;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.88rem;
    }

    .tree-list ul {
        list-style: none;
        margin: 0;
        padding-left: 1.15rem;
        border-left: 1px solid rgba(56, 189, 248, 0.18);
    }

    .tree-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        min-height: 30px;
        border-radius: 9px;
        padding: 0.18rem 0.45rem;
        color: var(--tag-text);
        white-space: nowrap;
    }

    .tree-row:hover {
        background: rgba(56, 189, 248, 0.09);
    }

    .tree-folder {
        color: var(--accent);
        font-weight: 850;
    }

    .tree-file {
        color: #cbd5e1;
    }

    .tree-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 22px;
        border-radius: 7px;
        flex: 0 0 22px;
        font-size: 0.82rem;
    }

    .folder-icon {
        background: var(--accent-soft);
        color: var(--accent-dark);
    }

    .file-icon {
        background: #1e293b;
        color: #94a3b8;
    }

    .empty-state {
        border: 1px dashed var(--line-strong);
        border-radius: 16px;
        background: rgba(17, 24, 39, 0.72);
        color: var(--muted);
        padding: 1.2rem;
    }

    .key-status {
        border: 1px solid rgba(34, 197, 94, 0.24);
        background: rgba(34, 197, 94, 0.1);
        color: #bbf7d0;
        border-radius: 10px;
        padding: 0.5rem 0.65rem;
        margin: 0.25rem 0 0.85rem;
        font-size: 0.86rem;
        font-weight: 700;
    }

    .analysis-copy {
        color: var(--muted);
        margin: -0.35rem 0 0.8rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


API_KEY_LABELS = {
    "OPENAI_API_KEY": "OpenAI API Key",
    "ANTHROPIC_API_KEY": "Anthropic API Key",
}


def _clean_env_value(value):
    return value.strip().strip('"').strip("'")


def load_env_keys(env_path=".env"):
    env_file_values = {}
    path = Path(env_path)

    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue

            key, value = stripped.split("=", 1)
            key = key.removeprefix("export ").strip()
            if key in API_KEY_LABELS:
                cleaned_value = _clean_env_value(value)
                if cleaned_value:
                    env_file_values[key] = cleaned_value

    values = {}
    sources = {}
    for key in API_KEY_LABELS:
        os_value = os.environ.get(key)
        if os_value:
            values[key] = os_value
            sources[key] = "environment"
        elif key in env_file_values:
            values[key] = env_file_values[key]
            sources[key] = ".env"

    return values, sources


def open_macos_folder_picker():
    script = (
        'POSIX path of (choose folder with prompt "Select a project folder" '
        'default location (POSIX file "/") with invisibles)'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except FileNotFoundError:
        return "", "osascript is not available on this machine."
    except subprocess.TimeoutExpired:
        return "", "The folder picker timed out."
    except Exception as exc:
        return "", str(exc)

    selected_path = result.stdout.strip()
    error_text = result.stderr.strip()

    if result.returncode == 0 and selected_path:
        return selected_path, None

    if "User canceled" in error_text:
        return "", None

    return "", error_text or f"osascript exited with code {result.returncode}."


def open_tkinter_folder_picker():
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected_path = filedialog.askdirectory(
            title="Select a project folder",
            initialdir="/",
            mustexist=True,
        )
        root.destroy()
        return selected_path, None
    except Exception as exc:
        return "", str(exc)


def open_folder_picker():
    errors = []

    if platform.system() == "Darwin":
        selected_path, error = open_macos_folder_picker()
        if selected_path or error is None:
            return selected_path, error
        errors.append(f"macOS picker: {error}")

    selected_path, error = open_tkinter_folder_picker()
    if selected_path or error is None:
        return selected_path, error

    errors.append(f"tkinter picker: {error}")
    return "", " ".join(errors)


# --- 1. Core Directory Scanning Functions ---
def get_directory_data(target_directory, exclude_list):
    root = Path(target_directory)
    data_list = []

    if not root.exists() or not root.is_dir():
        return None

    # Using rglob to index everything recursively
    for item in root.rglob("*"):
        if any(ex in item.parts for ex in exclude_list):
            continue

        item_type = "Folder" if item.is_dir() else "File"
        content = "<no content>"

        if item.is_file():
            try:
                text = item.read_text(encoding="utf-8", errors="ignore").strip()
                content = text if text else "<empty file>"
            except Exception:
                content = "<no content (unreadable/binary)>"

        # Calculate relative path to build tree easier
        try:
            rel_path = item.relative_to(root)
        except ValueError:
            rel_path = item

        item_dict = {
            "Type": item_type,
            "Path": str(item),
            "RelativePath": str(rel_path),
            "Content": content,
            "Name": item.name,
        }
        data_list.append(item_dict)

    return data_list


# --- 2. Helper to Build HTML Tree Layout ---
def generate_html_tree(target_path, exclude_list):
    root = Path(target_path)
    if not root.exists():
        return "<p class='empty-state'>Directory path does not exist.</p>"

    if not root.is_dir():
        return "<p class='empty-state'>The selected path is a file, not a directory.</p>"

    def build_nested_tree(dir_path):
        html_parts = ["<ul>"]
        try:
            # Sort directories first, then files alphabetically
            items = sorted(
                list(dir_path.iterdir()),
                key=lambda x: (not x.is_dir(), x.name.lower()),
            )
            visible_items = [item for item in items if item.name not in exclude_list]

            if not visible_items:
                html_parts.append(
                    "<li><span class='tree-row tree-file'>"
                    "<span class='tree-icon file-icon'>-</span>"
                    "<span>empty</span></span></li>"
                )

            for item in visible_items:
                safe_name = html.escape(item.name)
                if item.is_dir():
                    html_parts.append(
                        "<li>"
                        f"<span class='tree-row tree-folder'><span class='tree-icon folder-icon'>▸</span>{safe_name}</span>"
                    )
                    html_parts.append(build_nested_tree(item))
                    html_parts.append("</li>")
                else:
                    html_parts.append(
                        "<li>"
                        f"<span class='tree-row tree-file'><span class='tree-icon file-icon'>•</span>{safe_name}</span>"
                        "</li>"
                    )
        except Exception as e:
            safe_error = html.escape(str(e))
            html_parts.append(
                "<li><span class='tree-row tree-file'>"
                f"<span class='tree-icon file-icon'>!</span>Error reading layout: {safe_error}</span></li>"
            )
        html_parts.append("</ul>")
        return "".join(html_parts)

    safe_root = html.escape(root.name or str(root))
    return (
        "<div class='tree-shell'>"
        f"<div class='tree-root'><span class='root-icon'>⌂</span><span>{safe_root}</span></div>"
        f"<div class='tree-list'>{build_nested_tree(root)}</div>"
        "</div>"
    )


def render_skip_chips(folders_to_skip):
    chips = "".join(
        f"<span class='skip-chip'>{html.escape(folder)}</span>"
        for folder in folders_to_skip
    )
    st.markdown(
        f"<div class='skip-bar'><span class='skip-label'>Skipped folders</span>{chips}</div>",
        unsafe_allow_html=True,
    )


folders_to_skip = [
    ".git",
    "__pycache__",
    ".venv",
    "env",
    "myenv",
    "node_modules",
    ".DS_Store",
    "dist",
    ".env",
    "build",
]

if "repo_path" not in st.session_state:
    st.session_state["repo_path"] = ""

# --- 3. Sidebar: Configuration & API Keys ---
st.sidebar.title("Configuration ⚙️")

env_key_values, env_key_sources = load_env_keys()
for key, value in env_key_values.items():
    st.session_state[key] = value

for key, label in API_KEY_LABELS.items():
    source = env_key_sources.get(key)
    if source:
        st.sidebar.markdown(
            f"<div class='key-status'>{html.escape(label)} configured from {html.escape(source)}</div>",
            unsafe_allow_html=True,
        )
    else:
        entered_key = st.sidebar.text_input(
            label,
            type="password",
            value=st.session_state.get(key, ""),
        )
        if entered_key:
            st.session_state[key] = entered_key

selected_model = st.sidebar.selectbox("Choose AI Model", ["gpt-5.4-mini", "claude-haiku-4-5"])

# --- 4. Main UI App Header ---
st.markdown(
    """
<div class="workbench-shell">
    <div class="app-kicker">Local codebase workbench</div>
    <h1 class="app-title">AI Codebase Visualizer & Analyzer</h1>
    <p class="app-subtitle">
        Select a project folder, inspect the structure, and generate an architecture readout without leaving the workbench.
    </p>
</div>
""",
    unsafe_allow_html=True,
)

path_col, browse_col = st.columns([6, 1.15], gap="small", vertical_alignment="bottom")
with path_col:
    repo_path = st.text_input(
        "Project folder",
        value=st.session_state["repo_path"],
        placeholder="/Users/username/Projects/my-app",
        key="repo_path_input",
    )

with browse_col:
    if st.button("Browse", use_container_width=True):
        selected_path, picker_error = open_folder_picker()
        if picker_error:
            st.warning(f"Folder picker could not open: {picker_error} You can still paste the path manually.")
        elif selected_path:
            st.session_state["repo_path"] = selected_path
            st.rerun()

st.session_state["repo_path"] = repo_path.strip()

render_skip_chips(folders_to_skip)

repo_path = st.session_state["repo_path"]

if repo_path:
    target = Path(repo_path)
    if not target.exists():
        st.error("The specified path does not exist. Please check your spelling and try again.")
    elif not target.is_dir():
        st.error("The specified path is a file, not a directory.")
    else:
        # Layout columns: Left for Tree View, Right for Analysis Response
        col1, col2 = st.columns([1, 1.2], gap="large")

        with col1:
            tree_panel = st.container(border=True)
            with tree_panel:
                st.markdown(
                    "<div class='panel-title'><span class='panel-title-pill'>T</span>Structure Layout</div>",
                    unsafe_allow_html=True,
                )
                tree_html = generate_html_tree(repo_path, folders_to_skip)
                st.markdown(tree_html, unsafe_allow_html=True)

        with col2:
            analysis_panel = st.container(border=True)
            with analysis_panel:
                st.markdown(
                    "<div class='panel-title'><span class='panel-title-pill'>A</span>AI Analysis Actions</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<p class='analysis-copy'>Run a structured architecture pass over the visible project files.</p>",
                    unsafe_allow_html=True,
                )

                # Sparkle Analyze Button
                if st.button("✨ Analyze with AI", type="primary", use_container_width=True):
                    # Fetch directory content JSON payload
                    raw_data = get_directory_data(repo_path, folders_to_skip)

                    if not raw_data:
                        st.warning("No indexable code files found or error parsing layout.")
                    else:
                        # Clean up data payload size for the context window
                        payload = [
                            {"File": item["RelativePath"], "Content": item["Content"]}
                            for item in raw_data
                            if item["Type"] == "File"
                        ]

                        # Exact execution mapping and explanation prompt guidelines
                        system_prompt = (
                            "You are an expert software architecture mapping assistant. "
                            "Analyze the provided JSON code structure of this repository and deliver your report using the following structure:\n\n"
                            "1. **Core Summary**: A crisp, maximum two-line explanation outlining exactly what the project is and what core problem it solves.\n"
                            "2. **Project Purpose**: Briefly mention its high-level functionalities.\n"
                            "3. **Execution Pipeline Order**: Clear step-by-step breakdown detailing the order in which the files execute when the app boots up or interacts (e.g., Entrypoints, configurations, components, routing).\n"
                            "4. **Onboarding Guide**: Explicit, logical order a developer should read through this codebase file-by-file to comprehend it cleanly."
                        )

                        user_content = f"Here is the project repository data payload containing file paths and text bodies:\n\n{json.dumps(payload, indent=2)}"

                        with st.spinner(f"Processing codebase data with {selected_model}..."):
                            try:
                                response_text = ""

                                # Execution via OpenAI
                                if "gpt-5.4-mini" in selected_model:
                                    if not st.session_state.get("OPENAI_API_KEY"):
                                        st.error("Missing OpenAI API Key in the sidebar.")
                                    else:
                                        client = OpenAI(api_key=st.session_state["OPENAI_API_KEY"])
                                        completion = client.chat.completions.create(
                                            model="gpt-5.4-mini",
                                            messages=[
                                                {"role": "system", "content": system_prompt},
                                                {"role": "user", "content": user_content},
                                            ],
                                        )
                                        response_text = completion.choices[0].message.content

                                # Execution via Anthropic
                                elif "claude-haiku-4-5" in selected_model:
                                    if not st.session_state.get("ANTHROPIC_API_KEY"):
                                        st.error("Missing Anthropic API Key in the sidebar.")
                                    else:
                                        client = Anthropic(api_key=st.session_state["ANTHROPIC_API_KEY"])
                                        message = client.messages.create(
                                            model="claude-haiku-4-5",
                                            max_tokens=4000,
                                            system=system_prompt,
                                            messages=[
                                                {"role": "user", "content": user_content}
                                            ],
                                        )
                                        response_text = message.content[0].text

                                # Render output beautifully if fetched
                                if response_text:
                                    st.success("Analysis Complete!")
                                    st.markdown("---")
                                    st.markdown(response_text)

                            except Exception as e:
                                st.error(f"API Error occurred during structural inference: {str(e)}")
else:
    st.markdown(
        "<div class='empty-state'>Paste an absolute path or use Browse to initialize the project tree.</div>",
        unsafe_allow_html=True,
    )
