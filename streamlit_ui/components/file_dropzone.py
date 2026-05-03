"""File dropzone component for drag-and-drop file handling with path recognition"""

import streamlit as st
from pathlib import Path
from typing import Optional, Callable, List
import os


def file_dropzone(
    label: str = "📎 Drop files here or click to browse",
    accepted_types: Optional[List[str]] = None,
    key: str = "file_dropzone",
    on_file_received: Optional[Callable[[str, bytes, str], None]] = None
) -> Optional[dict]:
    """
    File dropzone component with path detection support
    
    Args:
        label: Label text for the dropzone
        accepted_types: List of accepted file extensions (e.g., ["txt", "py", "md"])
        key: Unique key for the component
        on_file_received: Callback function(file_name, file_content, file_path_guess)
        
    Returns:
        Dict with file info or None if no file uploaded
    """
    
    # Create a container for the dropzone
    container = st.container()
    
    with container:
        # Custom CSS for dropzone styling
        st.markdown("""
        <style>
        .file-dropzone {
            border: 2px dashed #ccc;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            background-color: #f9f9f9;
            transition: all 0.3s;
        }
        .file-dropzone:hover {
            border-color: #007bff;
            background-color: #f0f8ff;
        }
        .file-info {
            margin-top: 10px;
            padding: 10px;
            background-color: #e9ecef;
            border-radius: 5px;
            font-family: monospace;
            font-size: 0.9em;
        }
        .path-input {
            margin-top: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # File uploader with enhanced UI
        if accepted_types:
            type_str = f"Accepted: {', '.join(accepted_types)}"
        else:
            type_str = "All file types accepted"
            accepted_types = None
            
        st.markdown(f"""
        <div class="file-dropzone">
            <div style="font-size: 2em; margin-bottom: 10px;">📁</div>
            <div style="font-weight: bold; color: #333;">{label}</div>
            <div style="font-size: 0.8em; color: #666; margin-top: 5px;">{type_str}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Use native streamlit file uploader (drag & drop supported)
        uploaded_files = st.file_uploader(
            "",
            type=accepted_types,
            accept_multiple_files=True,
            key=f"{key}_uploader",
            label_visibility="collapsed"
        )
        
        # Handle multiple files
        if uploaded_files:
            # For now, process the first file (can be extended to handle all)
            if len(uploaded_files) > 1:
                st.info(f"📎 {len(uploaded_files)} files selected. Processing first file: {uploaded_files[0].name}")
            
            uploaded_file = uploaded_files[0]
            # Read file content
            file_content = uploaded_file.read()
            file_name = uploaded_file.name
            
            # Try to detect file encoding
            try:
                file_text = file_content.decode('utf-8')
                encoding = 'utf-8'
            except UnicodeDecodeError:
                try:
                    file_text = file_content.decode('gbk')
                    encoding = 'gbk'
                except UnicodeDecodeError:
                    file_text = None
                    encoding = 'binary'
            
            # Display file info
            st.markdown(f"""
            <div class="file-info">
                <strong>📄 {file_name}</strong><br>
                <span style="color: #666;">Size: {len(file_content):,} bytes | Encoding: {encoding}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Path input section - user can specify or guess the path
            st.markdown("<div class='path-input'><strong>📍 File Path (manual input or auto-detect):</strong></div>", 
                       unsafe_allow_html=True)
            
            # Try to auto-detect common paths
            suggested_paths = _guess_file_paths(file_name)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Path input with autocomplete suggestions
                if suggested_paths:
                    selected_path = st.selectbox(
                        "Select or type path:",
                        options=[""] + suggested_paths + ["📝 Manual input..."],
                        key=f"{key}_path_select",
                        format_func=lambda x: x if x != "" else "-- Select detected path or manual input --"
                    )
                    
                    if selected_path == "📝 Manual input...":
                        file_path = st.text_input(
                            "Enter full file path:",
                            value=f"./{file_name}",
                            key=f"{key}_manual_path",
                            placeholder="/path/to/your/file.txt"
                        )
                    elif selected_path:
                        file_path = selected_path
                    else:
                        file_path = None
                else:
                    file_path = st.text_input(
                        "Enter full file path:",
                        value=f"./{file_name}",
                        key=f"{key}_path_input",
                        placeholder="/path/to/your/file.txt",
                        help="Browser cannot access full local path. Please enter it manually."
                    )
            
            with col2:
                # Quick path presets
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📋 Current Dir", key=f"{key}_current_dir"):
                    st.session_state[f"{key}_path_input"] = f"./{file_name}"
                    st.rerun()
                if st.button("🏠 Home Dir", key=f"{key}_home_dir"):
                    home_path = Path.home() / file_name
                    st.session_state[f"{key}_path_input"] = str(home_path)
                    st.rerun()
            
            # File preview (collapsible)
            if file_text:
                with st.expander("👁️ Preview file content", expanded=False):
                    # Show first 1000 chars
                    preview = file_text[:2000] + "..." if len(file_text) > 2000 else file_text
                    st.code(preview, language=_detect_language(file_name))
            elif _is_image_file(file_name):
                # Image preview
                with st.expander("🖼️ Preview image", expanded=False):
                    st.image(file_content, caption=file_name, use_container_width=True)
            elif _is_video_file(file_name):
                # Video preview
                with st.expander("🎬 Preview video", expanded=False):
                    st.video(file_content, format=_get_video_format(file_name))
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            result = {
                "name": file_name,
                "content": file_content,
                "text": file_text,
                "encoding": encoding,
                "path": file_path or f"./{file_name}",
                "size": len(file_content)
            }
            
            with col1:
                if st.button("✅ Confirm & Use", key=f"{key}_confirm", type="primary", use_container_width=True):
                    if on_file_received:
                        on_file_received(file_name, file_content, result["path"])
                    st.success(f"✅ File ready: {result['path']}")
                    return result
            
            with col2:
                if st.button("📋 Copy Path", key=f"{key}_copy", use_container_width=True):
                    st.code(result["path"])
                    st.toast(f"Path copied: {result['path']}")
            
            with col3:
                if st.button("🗑️ Clear", key=f"{key}_clear", use_container_width=True):
                    st.session_state.pop(f"{key}_uploader", None)
                    st.rerun()
            
            return result
    
    return None


def _is_image_file(file_name: str) -> bool:
    """Check if file is an image based on extension"""
    ext = Path(file_name).suffix.lower()
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    return ext in image_extensions


def _is_video_file(file_name: str) -> bool:
    """Check if file is a video based on extension"""
    ext = Path(file_name).suffix.lower()
    video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
    return ext in video_extensions


def _get_video_format(file_name: str) -> str:
    """Get video MIME type format from file extension"""
    ext = Path(file_name).suffix.lower()
    format_map = {
        '.mp4': 'video/mp4',
        '.mkv': 'video/x-matroska',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.wmv': 'video/x-ms-wmv',
        '.flv': 'video/x-flv',
        '.webm': 'video/webm',
        '.m4v': 'video/mp4',
        '.3gp': 'video/3gpp',
    }
    return format_map.get(ext, 'video/mp4')


def _guess_file_paths(file_name: str) -> List[str]:
    """Try to guess common paths where the file might be located"""
    suggestions = []
    
    # Common directories to check
    common_dirs = [
        Path.home() / "Downloads",
        Path.home() / "Desktop",
        Path.home() / "Documents",
        Path.cwd(),
        Path.home() / "workspace",
        Path.home() / "workspace/github",
    ]
    
    for directory in common_dirs:
        if directory.exists():
            # Check if file exists directly
            direct_path = directory / file_name
            if direct_path.exists():
                suggestions.append(str(direct_path))
            
            # Recursively search (limit depth to avoid performance issues)
            try:
                for item in directory.rglob(file_name):
                    if item.is_file():
                        suggestions.append(str(item))
                        if len(suggestions) >= 5:  # Limit suggestions
                            break
            except PermissionError:
                continue
    
    # Remove duplicates while preserving order
    seen = set()
    unique_suggestions = []
    for path in suggestions:
        if path not in seen:
            seen.add(path)
            unique_suggestions.append(path)
    
    return unique_suggestions[:5]  # Return top 5 suggestions


def _detect_language(file_name: str) -> str:
    """Detect programming language from file extension"""
    ext = Path(file_name).suffix.lower()
    
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'jsx',
        '.tsx': 'tsx',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.json': 'json',
        '.xml': 'xml',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'markdown',
        '.sh': 'bash',
        '.sql': 'sql',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.m': 'matlab',
        '.ipynb': 'json',
        '.txt': 'text',
        '.log': 'text',
        '.csv': 'text',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.png': 'image',
        '.gif': 'image',
        '.webp': 'image',
        '.bmp': 'image',
        '.mp4': 'video',
        '.mkv': 'video',
        '.avi': 'video',
        '.mov': 'video',
        '.wmv': 'video',
        '.flv': 'video',
        '.webm': 'video',
        '.m4v': 'video',
        '.3gp': 'video',
    }
    
    return language_map.get(ext, 'text')


def render_file_dropzone_in_chat(
    chat_input_key: str = "chat_input",
    on_file_confirmed: Optional[Callable[[dict], None]] = None
):
    """Render file dropzone as part of chat interface"""
    
    with st.expander("📎 Attach File (Drag & Drop)", expanded=False):
        file_info = file_dropzone(
            label="Drop file here or click to browse",
            accepted_types=["txt", "py", "js", "md", "json", "yaml", "csv", "log", "jpg", "jpeg", "png", "gif", "webp", "bmp", "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v", "3gp"],
            key=chat_input_key,
            on_file_received=lambda name, content, path: _handle_file_for_chat(
                name, content, path, on_file_confirmed
            )
        )
        
        return file_info


def _handle_file_for_chat(file_name: str, file_content: bytes, file_path: str, 
                          callback: Optional[Callable[[dict], None]] = None):
    """Handle file received in chat context"""
    
    try:
        # Try to decode as text
        text_content = file_content.decode('utf-8')
    except UnicodeDecodeError:
        text_content = f"[Binary file: {len(file_content)} bytes]"
    
    file_data = {
        "name": file_name,
        "path": file_path,
        "content": text_content,
        "size": len(file_content)
    }
    
    # Add to session state for chat processing
    if 'pending_file_attachments' not in st.session_state:
        st.session_state['pending_file_attachments'] = []
    
    st.session_state['pending_file_attachments'].append(file_data)
    
    if callback:
        callback(file_data)
    
    st.success(f"📎 File attached: {file_name} ({file_path})")


def get_pending_attachments() -> List[dict]:
    """Get and clear pending file attachments"""
    attachments = st.session_state.get('pending_file_attachments', [])
    st.session_state['pending_file_attachments'] = []
    return attachments


def has_pending_attachments() -> bool:
    """Check if there are pending file attachments"""
    return len(st.session_state.get('pending_file_attachments', [])) > 0
