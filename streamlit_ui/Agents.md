python version: 3.11

conda activate safe_claw

For package import under streamlit_ui. follow below practice:
- start from streamlit_ui.safe_claw.
- Don`t from safe_claw.

For package import under safe_claw. follow below practice:
- start from safe_claw.
- Don`t from streamlit_ui.safe_claw.

## Debug Mode Configuration

### IntelliJ IDEA Debug Configuration

1. **Create Run/Debug Configuration:**
   - Go to `Run` → `Edit Configurations...`
   - Click `+` → `Python`
   - **Name:** `Streamlit Debug`
   - **Module name:** `streamlit`
   - **Parameters:** `run streamlit_ui/app.py --server.port 8502 --server.headless false --logger.level debug`
   - **Python interpreter:** Select your project's Python interpreter
   - **Working directory:** Set to your project root directory (e.g., `/path/to/python_gallery`)

2. **Environment Variables:**
   ```
   STREAMLIT_SERVER_PORT=8502
   STREAMLIT_SERVER_HEADLESS=false
   STREAMLIT_LOGGER_LEVEL=debug
   PYTHONPATH=./streamlit_ui
   ```

3. **Debugging Steps:**
   - Set breakpoints in `app.py` or any imported modules
   - Click the debug button (🐛) or press `Ctrl+D` (or `Cmd+D` on Mac)
   - Use IntelliJ's debugger: variables panel, console, step over/into
   - Streamlit automatically hot-reloads on file changes

### Common Debugging Locations
- `initialize_session_state()` function (lines ~50-120)
- LLM service initialization
- Memory manager setup
- Graph builder creation