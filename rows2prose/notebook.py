import uuid

import rows2prose.web
from IPython.display import HTML, display, update_display



def init_notebook_mode():
    display(HTML(
        rows2prose.web.header_content() + """
    <script>
      if (window.r2pQueue) {{
        window.r2pQueue.forEach(([k, f]) => f());
        window.r2pQueue = null;
      }}
    </script>
    """))


def js_refresh(element_id, df):
    return f"""
    (function() {{
      function update() {{
        document.getElementById("{element_id}")._r2pState.refresh({rows2prose.web.df_to_custom_json(df)});
      }}

      if (window.r2p) {{
        update();
      }} else {{
          if (!window.r2pQueue) {{
            window.r2pQueue = [];
          }}

          // Remove stale refreshes. (Avoid queueing a huge unnecessary work task)
          const k = "{element_id} update";
          window.r2pQueue = window.r2pQueue.filter(([k2, f]) => k2 != k);
          window.r2pQueue.push([k, update]);
      }}
    }})();
    </script>
    """


def visualize_snapshot(html_preamble, components, df):
    element_id = str(uuid.uuid1())
    components_str = "\n".join(components)

    s = f"""
    {html_preamble(element_id)}
    <script>
    function initialize() {{
      let onTableLoadedFunctions = [];

      let table;

      const container = document.getElementById("{element_id}");
      container._r2pState = {{
        refresh: function(encodedData) {{
          table = r2p.parseColumns(encodedData);
          onTableLoadedFunctions.forEach(onloaded => onloaded(table));
        }}
      }};

    {components_str}
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
    """

    display(HTML(s))

    # Reuse element ID as display ID, because it's convenient.
    display(HTML("<script>" + js_refresh(element_id, df) + "</script>"),
            display_id=element_id)
    return element_id


# To have reusable component code, we want to plug into layered events:
# - on table available
# - on selection changed

# Snapshot components only respond to the first one. And they have the option of
# simply running everything once, except that would mean parsing the expression
# string on every step.



def visualize_timeline(html_preamble, components, df):
    element_id = str(uuid.uuid1())
    components_str = "\n".join(components)

    s = f"""
{html_preamble(element_id)}
<script>
function initialize() {{
  function extractRows(arr, iRows) {{
    let selected = arr.slice(0, iRows.length);
    iRows.forEach((iRow, i) => {{
      selected[i] = arr[iRow];
    }});
    return selected;
  }}

  let renderRowsFunctions = [],
      renderTimeFunctions = [],
      onTableLoadedFunctions = [],
      table,
      sortedUniqueTimesteps;

  const container = document.getElementById("{element_id}");
  container._r2pState = {{
    refresh: function(encodedData) {{
      const tableBuffer = Uint8Array.from(atob(encodedData), c => c.charCodeAt(0));

      table = r2p.tableFromIPC(tableBuffer);
      sortedUniqueTimesteps = table["i_timestep"]
        .sort(d3.ascending).filter((d, i, a) => !i || d != a[i - 1]);

      onTableLoadedFunctions.forEach(onloaded => onloaded(table));

      d3.select(container).datum(sortedUniqueTimesteps).call(
        r2p.hiddenTimeState()
        .renderTimestep(t => {{
          const iTimestep = table["i_timestep"];

          let iRows = [];
          for (let i = 0; i < iTimestep.length; i++) {{
            if (iTimestep[i] == t) {{
              iRows.push(i);
            }}
          }}

          renderRowsFunctions.forEach(render => render(iRows));
        }})
       .renderTime((sortedUniqueTimesteps, index) => {{
          renderTimeFunctions.forEach(render => render(sortedUniqueTimesteps, index));
       }}));
    }}
  }};

{components_str}

  container._r2pState.refresh({rows2prose.web.df_to_custom_json(df)});
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
    """

    display(HTML(s))

    # Reuse element ID as display ID, because it's convenient.
    display(HTML("<script>" + js_refresh(element_id, df) + "</script>"),
            display_id=element_id)
    return element_id


def update_timeline(element_id, df):
    # Reuse element ID as display ID, because it's convenient.
    update_display(HTML("<script>" + js_refresh(element_id, df) + "</script>"),
                   display_id=element_id)


def update_snapshot(element_id, df):
    # This is currently identical to update_timeline, but that fact might change.
    return update_timeline(element_id, df)
