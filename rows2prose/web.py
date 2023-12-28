import os
import uuid
from pkg_resources import resource_string


def header_content():
    r2p_js = resource_string(
        'rows2prose', os.path.join('package_data', 'rows2prose.js')
    ).decode('utf-8')
    d3_js = resource_string(
        'rose2prose', os.path.join('package_data', 'd3.min.js')
    ).decode('utf-8')

    return f"""
<style>
div.r2p-output svg {{
  max-width: initial;
}}
</style>
<script>
  const r2p_undef_define = ("function"==typeof define);
  let r2p_prev_define = undefined;
  if (r2p_undef_define) {{
    r2p_prev_define = define;
    define = undefined;
  }}
  {d3_js}
  {r2p_js}
  if (r2p_undef_define) {{
    define = r2p_prev_define;
  }}
</script>"""



def time_control(class_name, labels=None):
    labels_str = (f" labels: {repr(labels)},"
                  if labels is not None
                  else "")
    if labels is None:
        labels = ["Start", "End"]

    return f"""
      (function() {{
        const element = container.querySelectorAll(".{class_name}")[0],
              component = r2p.timeControl()
                .onupdate(timestep => {{
                  d3.select(container).select(".timeState").node()._r2pState.selectTimestep(
                    timestep
                  );
                }});

        renderTimeFunctions.push(function(min, max, curr) {{
          d3.select(element).datum({{min: min, max: max, curr: curr,{labels_str}}}).call(component);
        }});
      }})();
    """


def position_view(class_name, key):
    return f"""
      (function() {{
        const element = container.querySelectorAll(".{class_name}")[0],
              component = r2p.positionView()
              .scale(d3.scaleLinear().domain([-1.3, 0.3]).range([0, 400]));

        renderTimestepFunctions.push(function (model) {{
          d3.select(element).datum(model["{key}"]).call(component);
        }});
      }})();
    """


def position_distribution_view(class_name, key):
    return f"""
      (function() {{
        const element = container.querySelectorAll(".{class_name}")[0];
        renderTimestepFunctions.push(function (model) {{
          const points = model["{key}"];
          let min = d3.min(points),
              max = d3.max(points);

          if (min == max) {{
            // Need a valid scale, so these need to be different.
            // Visualize each point as a low value.
            max += 1;
          }}

          const component = r2p.scalarDistributionView()
              .scale(d3.scaleLinear().domain([min, max]).range([0, 232]))
              .height(12)
              .fontSize(13)
              .useDataMin(true)
              .useDataMax(true);

          d3.select(element).datum(points).call(component);
        }});
      }})();
    """


def position_distribution_list_view(class_name, key):
    return f"""
      (function() {{
        const element = container.querySelectorAll(".{class_name}")[0];
        renderTimestepFunctions.push(function (model) {{
            const pointsLists = model["{key}"],
                  min = d3.min(pointsLists, points => d3.min(points)),
                  max = d3.max(pointsLists, points => d3.max(points)),
              component = r2p.scalarDistributionListView()
              .scale(d3.scaleLinear().domain([min, max]).range([0, 232]))
              .useDataMin(true)
              .useDataMax(true)
              .height(12)
              .fontSize(13);
          d3.select(element).datum({{pointsLists, min, max}}).call(component);
        }});
      }})();
    """


def expression_view(class_name, keys, text):
    return f"""
      (function() {{
        const kernelExpr = `{text}`,
              element = container.querySelectorAll(".{class_name}")[0],
              kernelKeys = {repr(keys)},
              component = r2p.expressionView(kernelExpr, kernelKeys);

        renderTimestepFunctions.push(function (model) {{
          d3.select(element).datum(model).call(component);
        }});
      }})();
    """


def expression_distribution_view(class_name, keys, text):
    return f"""
      (function() {{
        const kernelExpr = `{text}`,
              element = container.querySelectorAll(".{class_name}")[0],
              kernelKeys = {repr(keys)},
              component = r2p.expressionView(kernelExpr, kernelKeys).valueType("scalarDistribution");

        renderTimestepFunctions.push(function (model) {{
          d3.select(element).datum(model).call(component);
        }});
      }})();
    """


def expression_distribution_list_view(class_name, keys, text):
    return f"""
      (function() {{
        const kernelExpr = `{text}`,
              element = container.querySelectorAll(".{class_name}")[0],
              kernelKeys = {repr(keys)},
              component = r2p.expressionView(kernelExpr, kernelKeys).valueType("scalarDistributionList");

        renderTimestepFunctions.push(function (model) {{
          d3.select(element).datum(model).call(component);
        }});
      }})();
    """


def scalar_view(class_name, key):
    return f"""
      (function() {{
        const element = container.querySelectorAll(".{class_name}")[0],
              component = r2p.scalarView()
              .scale(d3.scaleLog().domain([1e-7, 5e0]).range([0, 400]))
              .eps(1e-7)
              .exponentFormat(true)
              .padRight(55)
              .height(12)
              .fontSize(13)
              .tfrac(2.7/3);

        renderTimestepFunctions.push(function (model) {{
          d3.select(element).datum(model["{key}"]).call(component);
        }});
      }})();
    """


def scalar_distribution_view(class_name, key):
    return f"""
      (function() {{
        const element = container.querySelectorAll(".{class_name}")[0];
        renderTimestepFunctions.push(function (model) {{
          const points = model["{key}"];
          let min = d3.min(points),
              max = d3.max(points);

          if (min == max) {{
            // Need a valid scale, so these need to be different.
            // Visualize each point as a low value.
            max *= 10;
          }}

          const component = r2p.scalarDistributionView()
              .scale(d3.scaleLog().domain([min, max]).range([0, 215]))
              .exponentFormat(true)
              .height(12)
              .fontSize(13);

          d3.select(element).datum(points).call(component);
        }});
      }})();
    """


def scalar_distribution_list_view(class_name, key):
    return f"""
      (function() {{
        const element = container.querySelectorAll(".{class_name}")[0];
        renderTimestepFunctions.push(function(model) {{
          const pointsLists = model["{key}"];

          let min = d3.min(pointsLists, points => d3.min(points)),
              max = d3.max(pointsLists, points => d3.max(points));

         if (min == max) {{
           // Need a valid scale, so these need to be different.
           // Visualize each point as a low value.
           max *= 10;
         }}

         const component = r2p.scalarDistributionListView()
              .scale(d3.scaleLog().domain([min, max]).range([0, 215]))
              .useDataMin(true)
              .useDataMax(true)
              .exponentFormat(true)
              .height(12)
              .fontSize(13);

          d3.select(element).datum({{pointsLists, min, max}}).call(component);
        }});
      }})();
    """


def scalar_timesteps_js(headers):
    return f"""
      const headers = {repr(headers)};
      const timesteps = encodedData
       .replace(/\\n$/, '') // strip any newline at the end of the string
       .split('\\n')
       .map(
          row => new Float32Array(Uint8Array.from(atob(row), c => c.charCodeAt(0)).buffer)
        ).map(
          row => Object.fromEntries(
            headers.map((header, i) => [header, row[i]])
        ));
    """


def scalar_snapshot_js(headers):
    return f"""
      {scalar_timesteps_js(headers)}
      if (timesteps.length != 1) {{
        throw "Expected single line";
      }}
      const snapshot = timesteps[0];
    """


def scalar_distribution_timesteps_js(headers, num_values_per_param):
    return f"""
      const numValuesPerParam = {num_values_per_param};
      const headers = {repr(headers)};
      const timesteps = encodedData
       .replace(/\\n$/, '') // strip any newline at the end of the string
       .split('\\n')
       .map(
         row => new Float32Array(Uint8Array.from(atob(row), c => c.charCodeAt(0)).buffer))
       .map(
           row => {{
             // Split row into numValuesPerParam chunks
              const chunks = [];
              for (let i = 0; i < row.length; i += numValuesPerParam) {{
                chunks.push(row.slice(i, i + numValuesPerParam));
              }}

             return Object.fromEntries(
               headers.map((header, i) => [header, chunks[i]]));
          }});
    """


def scalar_distribution_list_snapshot_js(headers, num_values_per_param):
    return f"""
      const numValuesPerParam = {repr(num_values_per_param)};
      const headers = {repr(headers)};
      const snapshot = Object.fromEntries(
        headers.map((header, i) => [header, []]));
      const models = encodedData
       .replace(/\\n$/, '') // strip any newline at the end of the string
       .split('\\n')
       .map(
         row => new Float32Array(Uint8Array.from(atob(row), c => c.charCodeAt(0)).buffer))
       .forEach(
           (row, iRow) => {{
             // Split row into numValuesPerParam chunks
              let iCol = 0;
              for (let i = 0; i < row.length; i += numValuesPerParam[iRow]) {{
                snapshot[headers[iCol]].push(row.slice(i, i + numValuesPerParam[iRow]));
                iCol++;
              }}
          }});
    """


def scalar_distribution_snapshot_js(headers, num_values_per_param):
    return f"""
      {scalar_distribution_timesteps_js(headers, num_values_per_param)}
      if (timesteps.length != 1) {{
        throw "Expected single line";
      }}
      const snapshot = timesteps[0];
    """


def visualize_timeline_html(html_preamble, encoded_to_timesteps, components, encoded_data):
    element_id = str(uuid.uuid1())
    components_str = "\n".join(components)

    return f"""
{html_preamble(element_id)}
<script>
(function() {{
  let renderTimestepFunctions = [],
      renderTimeFunctions = [],
      timeStateComponent = r2p.hiddenTimeState()
      .renderTimestep(model => {{
        renderTimestepFunctions.forEach(render => render(model))
      }})
      .renderTime((min, max, curr) => {{
        renderTimeFunctions.forEach(render => render(min, max, curr))
      }});

  const container = document.getElementById("{element_id}");

  {components_str}

  const encodedData = `{encoded_data}`;
  {encoded_to_timesteps}

  d3.select(container).datum(timesteps).call(timeStateComponent);
}})();
</script>"""


def visualize_snapshot_html(html_preamble, encoded_to_snapshot, components, encoded_data):
    element_id = str(uuid.uuid1())
    components_str = "\n".join(components)

    return f"""
{html_preamble(element_id)}
<script>
(function() {{
  let renderTimestepFunctions = [];

  const container = document.getElementById("{element_id}");

  {components_str}

  const encodedData = `{encoded_data}`;
  {encoded_to_snapshot}
  renderTimestepFunctions.forEach(render => render(snapshot));
}})();
</script>"""


def full_html(body):
    return f"""<!doctype html>
<html>
<head>
{header_content()}
</head>
<body>
{body}
</body>
</html>"""
