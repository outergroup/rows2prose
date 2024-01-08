import uuid

import rows2prose.web
from rows2prose.web import (Snapshot,
                            Timeline,
                            DistributionSnapshot,
                            DistributionTimeline,
                            DistributionListSnapshot)
import IPython.display as ipd



def init_notebook_mode():
    ipd.display(ipd.HTML(
        rows2prose.web.header_content() + """
    <script>
      if (window.r2pQueue) {{
        window.r2pQueue.forEach(([k, f]) => f());
        window.r2pQueue = null;
      }}
    </script>
    """))


def display(df, html, script):
    element_id = str(uuid.uuid1())
    ipd.display(ipd.HTML(f"""
<div id="{element_id}">{html}</div>
<script>
function renderStatic() {{
  let render = {script.static_js(df)};
  render(document.getElementById("{element_id}"));
}}

if (window.r2p) {{
  renderStatic();
}} else {{
    if (!window.r2pQueue) {{
      window.r2pQueue = [];
    }}

    window.r2pQueue.push(["", renderStatic]);
}}
</script>
"""))


class NotebookUpdater:
    def __init__(self, container_element_id, get_setdata_js):
        self.container_element_id = container_element_id
        self.notebook_display_id = str(uuid.uuid1())
        self.get_setdata_js = get_setdata_js
        self.is_set = False

    def set_data(self, df):
        dsp = (ipd.update_display if self.is_set else ipd.display)
        dsp(ipd.HTML(f"""
<script>
(function() {{
  function update() {{
    let render = {self.get_setdata_js(df)};
    render(document.getElementById("{self.container_element_id}"));
  }}

  if (window.r2p) {{
    update();
  }} else {{
      if (!window.r2pQueue) {{
        window.r2pQueue = [];
      }}

      // Remove stale refreshes. (Avoid queueing a huge unnecessary work task)
      const k = "{self.container_element_id} update";
      window.r2pQueue = window.r2pQueue.filter(([k2, f]) => k2 != k);
      window.r2pQueue.push([k, update]);
  }}
}})();
</script>
"""), display_id=self.notebook_display_id)
        self.is_set = True


def display_dynamic(html, script):
    element_id = str(uuid.uuid1())
    ipd.display(ipd.HTML(f"""
<div id="{element_id}">{html}</div>
<script>
function initialize() {{
  let render = {script.dynamic_initialize_js()};
  render(document.getElementById("{element_id}"));
}}

if (window.r2p) {{
  initialize();
}} else {{
    if (!window.r2pQueue) {{
      window.r2pQueue = [];
    }}

    window.r2pQueue.push(["", initialize]);
}}
</script>
"""))
    return NotebookUpdater(element_id, script.dynamic_set_data_js).set_data
