import streamlit as st
import json
from pathlib import Path
from openai import OpenAI
from anthropic import Anthropic

# Set page configuration
st.set_page_config(page_title="AI Codebase Visualizer & Analyzer", page_icon="✨", layout="wide")

# Tailwind CSS Integration for the file tree styling
st.markdown("""
<script src="https://cdn.tailwindcss.com"></script>
<style>
    .tree-folder { font-weight: 600; color: #4F46E5; }
    .tree-file { color: #374151; }
    .tree-container { font-family: monospace; background-color: #F9FAFB; padding: 15px; border-radius: 8px; border: 1px solid #E5E7EB; }
</style>
""", unsafe_allow_html=True)

# --- 1. Core Directory Scanning Functions ---
def get_directory_data(target_directory, exclude_list):
    root = Path(target_directory)
    data_list = []

    if not root.exists() or not root.is_dir():
        return None

    # Using rglob to index everything recursively
    for item in root.rglob('*'):
        if any(ex in item.parts for ex in exclude_list):
            continue
            
        item_type = "Folder" if item.is_dir() else "File"
        content = "<no content>"
        
        if item.is_file():
            try:
                text = item.read_text(encoding='utf-8', errors='ignore').strip()
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
            "Name": item.name
        }
        data_list.append(item_dict)
    
    return data_list

# --- 2. Helper to Build HTML Tree Layout ---
def generate_html_tree(target_path, exclude_list):
    root = Path(target_path)
    if not root.exists():
        return "<p class='text-red-500'>Directory path does not exist.</p>"
    
    def build_nested_tree(dir_path):
        html = "<ul class='pl-4 list-none border-l border-gray-200'>"
        try:
            # Sort directories first, then files alphabetically
            items = sorted(list(dir_path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
            for item in items:
                if item.name in exclude_list:
                    continue
                if item.is_dir():
                    html += f"<li class='my-1'><span class='tree-folder'>📁 {item.name}/</span>"
                    html += build_nested_tree(item)
                    html += "</li>"
                else:
                    html += f"<li class='my-0.5 tree-file'>📄 {item.name}</li>"
        except Exception as e:
            html += f"<li class='text-red-400'>Error reading layout: {str(e)}</li>"
        html += "</ul>"
        return html

    return f"<div class='tree-container'><span class='tree-folder'>🏠 {root.name}/</span>{build_nested_tree(root)}</div>"

# --- 3. Sidebar: Configuration & API Keys ---
st.sidebar.title("Configuration ⚙️")

openai_key = st.sidebar.text_input("OpenAI API Key", type="password", value=st.session_state.get("OPENAI_API_KEY", ""))
anthropic_key = st.sidebar.text_input("Anthropic API Key", type="password", value=st.session_state.get("ANTHROPIC_API_KEY", ""))

# Persist keys in session state
if openai_key: st.session_state["OPENAI_API_KEY"] = openai_key
if anthropic_key: st.session_state["ANTHROPIC_API_KEY"] = anthropic_key

selected_model = st.sidebar.selectbox("Choose AI Model", ["gpt-5.4-mini", "claude-haiku-4-5"])

folders_to_skip = ['.git', '__pycache__', '.venv', 'myenv', 'node_modules', '.DS_Store', 'dist', '.env', 'build']

# --- 4. Main UI App Header ---
st.title("🖥️ AI Codebase Visualizer & Analyzer")
st.write("Provide your local project path to visualize its structure and instantly analyze it using frontier mini LLMs.")

# Path Input
repo_path = st.text_input("Enter local project folder absolute path:", placeholder="/Users/username/Projects/my-app")

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
            st.subheader("Structure Layout")
            # Build and render the HTML Tree structure instantly
            tree_html = generate_html_tree(repo_path, folders_to_skip)
            st.markdown(tree_html, unsafe_allow_html=True)
            
        with col2:
            st.subheader("AI Analysis Actions")
            
            # Sparkle Analyze Button
            if st.button("✨ Analyze with AI", type="primary", use_container_width=True):
                # Fetch directory content JSON payload
                raw_data = get_directory_data(repo_path, folders_to_skip)
                
                if not raw_data:
                    st.warning("No indexable code files found or error parsing layout.")
                else:
                    # Clean up data payload size for the context window
                    payload = [{"File": item["RelativePath"], "Content": item["Content"]} for item in raw_data if item["Type"] == "File"]
                    
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
                                            {"role": "user", "content": user_content}
                                        ]
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
                                        ]
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
    st.info("Input an absolute directory path to visually initialize the tree workflow view.")