import base64
import json
import os
import uuid
from pkg_resources import resource_string


def header_content():
    r2p_js = resource_string(
        'rows2prose', os.path.join('package_data', 'rows2prose.browser.js')
    ).decode('utf-8')
    d3_js = resource_string(
        'rows2prose', os.path.join('package_data', 'd3.min.js')
    ).decode('utf-8')

    return f"""
<style>
div.r2p-output svg {{
  max-width: initial;
}}
</style>
<script>
  var r2p_undef_define = ("function"==typeof define),
      r2p_prev_define = undefined;
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



def time_control(class_name):
    return f"""
  (function() {{
    const element = container.querySelectorAll(".{class_name}")[0],
          component = r2p.timeControl()
          .onupdate(iTimestep => {{
            d3.select(container).select(".timeState").node()._r2pState.selectTimestep(
              iTimestep
            );
          }});

    renderTimeFunctions.push(function(sortedUniqueTimesteps, index) {{
      d3.select(element).datum({{sortedUniqueTimesteps, index}}).call(component);
    }});
  }})();
    """



def snapshot_position_view(class_name, key):
    return f"""
  (function() {{
    const element = container.querySelectorAll(".{class_name}")[0];

    onTableLoadedFunctions.push(() => {{
      d3.select(element)
        .datum(table["{key}"][0])
        .call(r2p.positionView()
          .scale(d3.scaleLinear().domain([-1, 1]).range([0, 232])));
    }});
  }})();
    """


def timeline_position_view(class_name, key):
    return f"""
  (function() {{
    const element = container.querySelectorAll(".{class_name}")[0];

    let component;
    onTableLoadedFunctions.push(() => {{
      const [globalMin, globalMax] = d3.extent(table["{key}"]),
             min = globalMin;
             // Need a valid scale, so these need to be different.
             max = (globalMin != globalMax)
               ? globalMax
               : globalMax + 1;  // Visualize each point as a low value.
      component = r2p.positionView()
        .scale(d3.scaleLinear().domain([min, max]).range([0, 232]));
    }});

    renderRowsFunctions.push(function (iRows) {{
      d3.select(element)
        .datum(table["{key}"][iRows[0]])
        .call(component);
    }});
  }})();
    """


def timeline_position_distribution_view(class_name, key):
    return f"""
  (function() {{
    const element = container.querySelectorAll(".{class_name}")[0];

    let component;
    onTableLoadedFunctions.push(() => {{
      const [globalMin, globalMax] = d3.extent(table["{key}"]),
            min = globalMin,
            // Need a valid scale, so these need to be different.
            max = (globalMin != globalMax)
            ? globalMax
            : globalMax + 1;  // Visualize each point as a low value.

      component = r2p.scalarDistributionView()
        .scale(d3.scaleLinear().domain([min, max]).range([0, 232]))
        .height(12)
        .fontSize(13);
    }});

    renderRowsFunctions.push(function (iRows) {{
      d3.select(element)
        .datum(extractRows(table["{key}"], iRows))
        .call(component);
    }});
  }})();
    """


def snapshot_position_distribution_list_view(class_name, key):
    return f"""
  (function() {{
    const element = container.querySelectorAll(".{class_name}")[0];

    onTableLoadedFunctions.push(() => {{
      const mean = table["{key}"];
      let [min, max] = d3.extent(mean);
      if (min == max) {{
        // Need a valid scale, so these need to be different.
        // Visualize each point as a low value.
        max += 1;
      }}

      d3.select(element)
        .datum({{values: mean, iConfigs: iConfig, nConfigs, min, max}})
        .call(r2p.scalarDistributionListView()
              .scale(d3.scaleLinear().domain([min, max]).range([0, 232]))
              .useDataMin(true)
              .useDataMax(true)
              .height(12)
              .fontSize(13));
    }});
  }})();
    """


def snapshot_expression_view(class_name, keys, text):
    return f"""
  (function() {{
    const kernelExpr = `{text}`,
          kernelKeys = {repr(keys)},
          element = container.querySelectorAll(".{class_name}")[0],
          component = r2p.expressionView(kernelExpr, kernelKeys).valueType("scalar");

    onTableLoadedFunctions.push(() => {{
      const model = Object.fromEntries(
        kernelKeys.map(k => [k, table[k][0]])
      );
      d3.select(element).datum(model).call(component);
    }});
  }})();
    """


def timeline_expression_view(class_name, keys, text):
    return f"""
  (function() {{
    const kernelExpr = `{text}`,
          kernelKeys = {repr(keys)},
          element = container.querySelectorAll(".{class_name}")[0],
          component = r2p.expressionView(kernelExpr, kernelKeys).valueType("scalar");

    renderRowsFunctions.push(function (iRows) {{
      const model = Object.fromEntries(
        kernelKeys.map(k => [k, table[k][iRows[0]]])
      );

      d3.select(element).datum(model).call(component);
    }});
  }})();
    """


def timeline_expression_distribution_view(class_name, keys, text):
    return f"""
  (function() {{
    const kernelExpr = `{text}`,
          kernelKeys = {repr(keys)},
          element = container.querySelectorAll(".{class_name}")[0],
          component = r2p.expressionView(kernelExpr, kernelKeys).valueType("scalarDistribution");

    renderRowsFunctions.push(function (iRows) {{
      const model = Object.fromEntries(
        kernelKeys.map(k => [k, extractRows(table[k], iRows)])
      );

      d3.select(element).datum(model).call(component);
    }});
  }})();
    """


def snapshot_expression_distribution_list_view(class_name, keys, text):
    return f"""
  (function() {{
    const element = container.querySelectorAll(".{class_name}")[0],
          kernelExpr = `{text}`,
          kernelKeys = {repr(keys)},
          component = r2p.expressionView(kernelExpr, kernelKeys)
            .valueType("scalarDistributionList")

    onTableLoadedFunctions.push(() => {{
      d3.select(element)
        .datum(Object.fromEntries(
          kernelKeys.map(k => {{
            const param = table[k],
                  [min, max] = d3.extent(param);
            return [k, {{values: param, iConfigs: iConfig, nConfigs, min, max}}];
          }})
        ))
        .call(component);
    }});
   }})();
    """


def snapshot_scalar_view(class_name, key):
    return f"""
  (function() {{
    const element = container.querySelectorAll(".{class_name}")[0];

    onTableLoadedFunctions.push(() => {{
      d3.select(element)
        .datum(table["{key}"][0])
        .call(r2p.scalarView()
          .scale(d3.scaleLog().domain([1e-7, 2.0]).range([0, 215]))
          .eps(1e-7)
          .exponentFormat(true)
          .padRight(55)
          .height(12)
          .fontSize(13)
          .tfrac(2.7/3));
    }})
  }})();
    """


def timeline_scalar_view(class_name, key):
    return f"""
  (function() {{
    const element = container.querySelectorAll(".{class_name}")[0];

    let component;
    onTableLoadedFunctions.push(() => {{
      const [globalMin, globalMax] = d3.extent(table["{key}"]),
            min = globalMin,
            // Need a valid scale, so these need to be different.
            max = (globalMin != globalMax)
            ? globalMax
            : globalMax * 10;  // Visualize each point as a low value.
      component = r2p.scalarView()
          .scale(d3.scaleLog().domain([min, max]).range([0, 215]))
          .eps(1e-7)
          .exponentFormat(true)
          .padRight(55)
          .height(12)
          .fontSize(13)
          .tfrac(2.7/3);
    }})

    renderRowsFunctions.push(function (iRows) {{
      d3.select(element)
        .datum(table["{key}"][iRows[0]])
        .call(component);
    }});
  }})();
    """


def timeline_scalar_distribution_view(class_name, key):
    return f"""
  (function() {{
    const element = container.querySelectorAll(".{class_name}")[0];

    let component;
    onTableLoadedFunctions.push(() => {{
      const [globalMin, globalMax] = d3.extent(table["{key}"]),
            min = globalMin,
            // Need a valid scale, so these need to be different.
            max = (globalMin != globalMax)
            ? globalMax
            : globalMax * 10;  // Visualize each point as a low value.
      component = r2p.scalarDistributionView()
        .scale(d3.scaleLog().domain([min, max]).range([0, 215]))
        .exponentFormat(true)
        .height(12)
        .fontSize(13);
    }});

    renderRowsFunctions.push(function (iRows) {{
      d3.select(element)
        .datum(extractRows(table["{key}"], iRows))
        .call(component);
    }});
  }})();
    """


def snapshot_scalar_distribution_list_view(class_name, key):
    return f"""
  (function() {{
    const element = container.querySelectorAll(".{class_name}")[0];

    onTableLoadedFunctions.push(() => {{
      const values = table["{key}"];
      let [min, max] = d3.extent(values);
      if (min == max) {{
        // Need a valid scale, so these need to be different.
        // Visualize each point as a low value.
        max *= 10;
      }}

      d3.select(element)
        .datum({{values, iConfigs: iConfig, nConfigs, min, max}})
        .call(r2p.scalarDistributionListView()
          .scale(d3.scaleLog().domain([min, max]).range([0, 215]))
          .useDataMin(true)
          .useDataMax(true)
          .exponentFormat(true)
          .height(12)
          .fontSize(13));
    }});
  }})();
    """


def df_to_dict(df):
    """
    Returns {"columnName1": {"type": "float32", "data": "BASE64ENCODED_DATA1"},
             "columnName2": {"type": "float32", "data": "BASE64ENCODED_DATA2"},
             ...}
    using the column's type to determine "type".
    """
    return {
        col: {
            "type": str(df[col].dtype),
            "data": base64.b64encode(df[col].values).decode("utf-8")
        }
        for col in df.columns
    }



def df_to_custom_json(df):
    """
    Returns {"columnName1": {"type": "float32", "data": "BASE64ENCODED_DATA1"},
             "columnName2": {"type": "float32", "data": "BASE64ENCODED_DATA2"},
             ...}
    using the column's type to determine "type".
    """
    return json.dumps(df_to_dict(df))


def visualize_timeline_html(html_preamble, components, df):
    element_id = str(uuid.uuid1())
    components_str = "\n".join(components)

    return f"""
{html_preamble(element_id)}
<script>
(function() {{
  function extractRows(arr, iRows) {{
    let selected = arr.slice(0, iRows.length);
    iRows.forEach((iRow, i) => {{
      selected[i] = arr[iRow];
    }});
    return selected;
  }}

  let renderRowsFunctions = [],
      renderTimeFunctions = [],
      onTableLoadedFunctions = [];

  let table, sortedUniqueTimesteps;

  const container = document.getElementById("{element_id}"),
        timeStateComponent = r2p.hiddenTimeState()
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
        }});

  {components_str}

  table = r2p.parseColumns({df_to_custom_json(df)});
  sortedUniqueTimesteps = table["i_timestep"]
    .sort(d3.ascending).filter((d, i, a) => !i || d != a[i - 1]);
  onTableLoadedFunctions.forEach(onloaded => onloaded());

  d3.select(container).datum(sortedUniqueTimesteps).call(timeStateComponent);
}})();
</script>"""


def visualize_snapshot_distribution_lists_html(html_preamble, components, df):
    element_id = str(uuid.uuid1())
    components_str = "\n".join(components)

    return f"""
{html_preamble(element_id)}
<script>
(function() {{

  const container = document.getElementById("{element_id}");

  let onTableLoadedFunctions = [];

  let table, iConfig, nConfigs;

  {components_str}

  table = r2p.parseColumns({df_to_custom_json(df)});
  iConfig = table["i_config"],
  nConfigs = d3.max(iConfig) + 1;
  onTableLoadedFunctions.forEach(onloaded => onloaded());
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
