"""Check the actual Streamlit app starts, not just that Python modules import."""
from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_dashboard_initial_screen_renders():
    target=Path(__file__).resolve().parents[1]/"app"/"main.py"
    app=AppTest.from_file(str(target),default_timeout=25).run()
    assert not app.exception, [str(item.message) for item in app.exception]
    assert len(app.text_input)>=1
    assert len(app.selectbox)==2
    assert any("AeroPulse" in str(item.value) for item in app.markdown)
