import abc
import base64
import json
import os
import uuid
from pkg_resources import resource_string

import numpy as np


def df_to_dict(df):
    """
    Returns {"columnName1": {"type": "float32", "data": "BASE64ENCODED_DATA1"},
             "columnName2": {"type": "float32", "data": "BASE64ENCODED_DATA2"},
             ...}
    using the column's type to determine "type".
    """
    df2 = df.copy()
    # convert any int64 to int32, since javascript BigInts cause problems in
    # code that expects javascript Numbers
    for col in df2.columns:
        if df2[col].dtype == np.int64:
            df2[col] = df2[col].astype(np.int32)
        elif df2[col].dtype == np.uint64:
            df2[col] = df2[col].astype(np.uint32)

    return {
        col: {
            "type": str(df2[col].dtype),
            "data": base64.b64encode(
                np.ascontiguousarray(df2[col].values)).decode("utf-8")
        }
        for col in df2.columns
    }



def df_to_custom_json(df):
    """
    Returns {"columnName1": {"type": "float32", "data": "BASE64ENCODED_DATA1"},
             "columnName2": {"type": "float32", "data": "BASE64ENCODED_DATA2"},
             ...}
    using the column's type to determine "type".
    """
    return json.dumps(df_to_dict(df))



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



def _time_control(class_name, prefix="Step"):
    return f"""
(function() {{
  const element = container.querySelectorAll(".{class_name}")[0],
        component = r2p.timeControl()
        .prefix("{prefix}")
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

class ScriptBuilder(abc.ABC):
    @abc.abstractmethod
    def static_js(self, df):
        pass

    @abc.abstractmethod
    def dynamic_initialize_js(self, df):
        pass

    @abc.abstractmethod
    def dynamic_set_data_js(self, df):
        pass


class Snapshot(ScriptBuilder):
    def __init__(self, *controls):
        self.controls = controls

    def static_js(self, df):
        controls_js = "\n".join(self.controls)
        return f"""
function(container) {{
  let onTableLoadedFunctions = [],
      table;

  {controls_js}

  table = r2p.parseColumns({df_to_custom_json(df)});
  onTableLoadedFunctions.forEach(onloaded => onloaded());
}}
"""

    def dynamic_initialize_js(self):
        controls_js = "\n".join(self.controls)
        return f"""
function(container) {{
  let onTableLoadedFunctions = [],
      table;
  container._r2pState = {{
    refresh: function(encodedData) {{
      table = r2p.parseColumns(encodedData);
      onTableLoadedFunctions.forEach(onloaded => onloaded(table));
    }}
  }};

  {controls_js}
}}
"""

    def dynamic_set_data_js(self, df):
        return f"""
function(container) {{
  container._r2pState.refresh({df_to_custom_json(df)});
}}
"""

    @classmethod
    def position_view(cls, class_name, key):
        return f"""
(function() {{
  const element = container.querySelectorAll(".{class_name}")[0];

  onTableLoadedFunctions.push(() => {{
    element
      .data(keys.map(k => table[k][0]))
      .call(r2p.positionView()
        .scale(d3.scaleLinear().domain([-1, 1]).range([0, 232])));
  }});
}})();
"""

    @classmethod
    def expression_view(cls, class_name, keys, text):
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

    @classmethod
    def positive_scalar_view(cls, class_name, log_scale=False):
        return f"""
(function() {{
  const element = d3.select(container).selectAll(".{class_name}"),
        keys = element.nodes().map(e => e.getAttribute("data-key"));
  onTableLoadedFunctions.push(() => {{
    const globalMin = d3.min(keys, k => d3.min(table[k])),
          globalMax = d3.max(keys, k => d3.max(table[k])),
          min = globalMin,
          // Need a valid scale, so these need to be different.
          max = (globalMin != globalMax)
          ? globalMax
          : {"globalMax * 10" if log_scale else "globalMax + 1"};  // Visualize each point as a low value.

    element
      .data(keys.map(k => table[k][0]))
      .call(r2p.scalarView()
        .scale(d3.{"scaleLog()" if log_scale else "scaleLinear()"}
          .domain([{"1e-7" if log_scale else "0"}, max]).range([0, 215]))
        {".exponentFormat(true)" if log_scale else ""}
        .eps(1e-7)
        .padRight(55)
        .height(12)
        .fontSize(13)
        .tfrac(2.7/3));
  }});
}})();
"""


class Timeline(ScriptBuilder):
    def __init__(self, *controls, i_timestep_column="i_timestep"):
        self.controls = controls
        self.i_timestep_column = i_timestep_column

    def static_js(self, df):
        controls_js = "\n".join(self.controls)
        return f"""
function(container) {{
  let renderRowsFunctions = [],
      renderTimeFunctions = [],
      onTableLoadedFunctions = [],
      table,
      sortedUniqueTimesteps;

  const timeStateComponent = r2p.hiddenTimeState()
        .renderTimestep(t => {{
          const iTimestep = table["{self.i_timestep_column}"];

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

  {controls_js}

  table = r2p.parseColumns({df_to_custom_json(df)});
  sortedUniqueTimesteps = table["{self.i_timestep_column}"]
    .sort(d3.ascending).filter((d, i, a) => !i || d != a[i - 1]);
  onTableLoadedFunctions.forEach(onloaded => onloaded());

  d3.select(container).datum(sortedUniqueTimesteps).call(timeStateComponent);
}}
"""

    def dynamic_initialize_js(self):
        controls_js = "\n".join(self.controls)
        return f"""
function(container) {{
  let renderRowsFunctions = [],
      renderTimeFunctions = [],
      onTableLoadedFunctions = [],
      table,
      sortedUniqueTimesteps;

  container._r2pState = {{
    refresh: function(encodedData) {{
      table = r2p.parseColumns(encodedData);
      sortedUniqueTimesteps = table["{self.i_timestep_column}"]
        .sort(d3.ascending).filter((d, i, a) => !i || d != a[i - 1]);

      onTableLoadedFunctions.forEach(onloaded => onloaded(table));

      d3.select(container).datum(sortedUniqueTimesteps).call(
        r2p.hiddenTimeState()
        .renderTimestep(t => {{
          const iTimestep = table["{self.i_timestep_column}"];

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

{controls_js}

}}
"""

    def dynamic_set_data_js(self, df):
        return f"""
function(container) {{
  container._r2pState.refresh({df_to_custom_json(df)});
}}
"""

    @classmethod
    def time_control(cls, class_name, prefix="Step"):
        return _time_control(class_name, prefix)

    @classmethod
    def position_view(cls, class_name, key):
        return f"""
(function() {{
  const element = container.querySelectorAll(".{class_name}")[0];

  let component;
  onTableLoadedFunctions.push(() => {{
    const globalMin = d3.min(keys, k => d3.min(table[k])),
          globalMax = d3.max(keys, k => d3.max(table[k])),
           min = globalMin;
           // Need a valid scale, so these need to be different.
           max = (globalMin != globalMax)
             ? globalMax
             : globalMax + 1;  // Visualize each point as a low value.
    component = r2p.positionView()
      .scale(d3.scaleLinear().domain([min, max]).range([0, 232]));
  }});

  renderRowsFunctions.push(function (iRows) {{
    element
      .data(keys.map(k => table[k][iRows[0]]))
      .call(component);
  }});
}})();
"""

    @classmethod
    def expression_view(cls, class_name, keys, text):
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

    @classmethod
    def positive_scalar_view(cls, class_name, log_scale=False):
        return f"""
(function() {{
  const element = d3.select(container).selectAll(".{class_name}"),
        keys = element.nodes().map(e => e.getAttribute("data-key"));

  let component;
  onTableLoadedFunctions.push(() => {{
    const globalMin = d3.min(keys, k => d3.min(table[k])),
          globalMax = d3.max(keys, k => d3.max(table[k])),
          min = globalMin,
          // Need a valid scale, so these need to be different.
          max = (globalMin != globalMax)
          ? globalMax
          : {"globalMax * 10" if log_scale else "globalMax + 1"};  // Visualize each point as a low value.
    component = r2p.scalarView()
        .scale(d3.{"scaleLog()" if log_scale else "scaleLinear()"}.domain([{"1e-7" if log_scale else "0"}, max]).range([0, 215]))
        .eps(1e-7)
        {".exponentFormat(true)" if log_scale else ""}
        .padRight(55)
        .height(12)
        .fontSize(13)
        .tfrac(2.7/3);
  }})

  renderRowsFunctions.push(function (iRows) {{
    element
      .data(keys.map(k => table[k][iRows[0]]))
      .call(component);
  }});
}})();
"""


class DistributionSnapshot(ScriptBuilder):
    def __init__(self, *controls):
        self.controls = controls

    def static_js(self, df):
        controls_js = "\n".join(self.controls)
        return f"""
function(container) {{
  let onTableLoadedFunctions = [],
      table;

  {controls_js}

  table = r2p.parseColumns({df_to_custom_json(df)});
  onTableLoadedFunctions.forEach(onloaded => onloaded());
}}
"""

    def dynamic_initialize_js(self):
        controls_js = "\n".join(self.controls)
        return f"""
function(container) {{
  let onTableLoadedFunctions = [],
      table;
  container._r2pState = {{
    refresh: function(encodedData) {{
      table = r2p.parseColumns(encodedData);
      onTableLoadedFunctions.forEach(onloaded => onloaded(table));
    }}
  }};

  {controls_js}
}}
"""

    def dynamic_set_data_js(self, df):
        return f"""
function(container) {{
  container._r2pState.refresh({df_to_custom_json(df)});
}}
"""

    @classmethod
    def scalar_view(cls, class_name, log_scale=False):
        return f"""
(function() {{
  const element = d3.select(container).selectAll(".{class_name}"),
        keys = element.nodes().map(e => e.getAttribute("data-key"));
  onTableLoadedFunctions.push(() => {{
    const globalMin = d3.min(keys, k => d3.min(table[k])),
          globalMax = d3.max(keys, k => d3.max(table[k])),
          min = globalMin,
          // Need a valid scale, so these need to be different.
          max = (globalMin != globalMax)
          ? globalMax
          : {"globalMax * 10" if log_scale else "globalMax + 1"};  // Visualize each point as a low value.

    element
      .data(keys.map(k => table[k]))
      .call(r2p.scalarDistributionView()
        .scale(d3.{"scaleLog()" if log_scale else "scaleLinear()"}.domain([min, max]).range([0, 215]))
        {".exponentFormat(true)" if log_scale else ""}
        .useDataMax(true)
        .height(12)
        .fontSize(13));
  }});
}})();
"""

    @classmethod
    def expression_view(class_name, keys, text):
        raise NotImplementedError()


class DistributionListSnapshot(ScriptBuilder):
    def __init__(self, *controls, i_config_column="i_config"):
        self.controls = controls
        self.i_config_column = i_config_column

    def static_js(self, df):
        controls_js = "\n".join(self.controls)
        return f"""
function(container) {{
  let onTableLoadedFunctions = [],
      table,
      iConfig,
      nConfigs;

  {controls_js}

  table = r2p.parseColumns({df_to_custom_json(df)});
  iConfig = table["{self.i_config_column}"],
  nConfigs = d3.max(iConfig) + 1,
  onTableLoadedFunctions.forEach(onloaded => onloaded());
}}
"""

    def dynamic_initialize_js(self):
        raise NotImplementedError()

    def dynamic_set_data_js(self, df):
        return f"""
function(container) {{
  container._r2pState.refresh({rows2prose.web.df_to_custom_json(df)});
}}
"""

    @classmethod
    def scalar_view(cls, class_name, height=35, point_radius=2, log_scale=False):
        return f"""
(function() {{
  const element = d3.select(container).selectAll(".{class_name}"),
        keys = element.nodes().map(e => e.getAttribute("data-key"));

  onTableLoadedFunctions.push(() => {{
    const globalMin = d3.min(keys, k => d3.min(table[k])),
          globalMax = d3.max(keys, k => d3.max(table[k])),
          min = globalMin,
          // Need a valid scale, so these need to be different.
          max = (globalMin != globalMax)
          ? globalMax
          : {"globalMax * 10" if log_scale else "globalMax + 1"};  // Visualize each point as a low value.

    element
      .data(keys.map(k => {{ return {{ values: table[k], iConfigs: iConfig, nConfigs, min, max }}; }}))
      .call(r2p.scalarDistributionListView()
        .scale(d3.{"scaleLog()" if log_scale else "scaleLinear()"}.domain([min, max]).range([0, 215]))
        .useDataMin(true)
        .useDataMax(true)
        {".exponentFormat(true)" if log_scale else ""}
        .pointRadius({point_radius})
        .height({height})
        .fontSize("13px"));
  }});
}})();
"""

    @classmethod
    def expression_view(class_name, keys, text):
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

    @classmethod
    def position_view(cls, class_name):
        return f"""
(function() {{
  const element = d3.select(container).selectAll(".{class_name}"),
        keys = element.nodes().map(e => e.getAttribute("data-key"));

  onTableLoadedFunctions.push(() => {{
    const globalMin = d3.min(keys, k => d3.min(table[k])),
          globalMax = d3.max(keys, k => d3.max(table[k])),
          min = globalMin,
          // Need a valid scale, so these need to be different.
          max = (globalMin != globalMax)
          ? globalMax
          : {"globalMax * 10" if log_scale else "globalMax + 1"};  // Visualize each point as a low value.

    d3.select(element)
      .data(keys.map(k => {{ return {{ values: table[k], iConfigs: iConfig, nConfigs, min, max }}; }}))
      .call(r2p.scalarDistributionListView()
            .scale(d3.scaleLinear().domain([min, max]).range([0, 232]))
            .useDataMin(true)
            .useDataMax(true)
            .height(12)
            .fontSize(13));
  }});
}})();
"""


class DistributionTimeline(ScriptBuilder):
    def __init__(self, *controls, i_timestep_column="i_timestep"):
        self.controls = controls
        self.i_timestep_column = i_timestep_column

    def static_js(self, df):
        controls_js = "\n".join(self.controls)
        return f"""
function(container) {{
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

  const timeStateComponent = r2p.hiddenTimeState()
        .renderTimestep(t => {{
          const iTimestep = table["{self.i_timestep_column}"];

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

  {controls_js}

  table = r2p.parseColumns({df_to_custom_json(df)});
  sortedUniqueTimesteps = table["{self.i_timestep_column}"]
    .sort(d3.ascending).filter((d, i, a) => !i || d != a[i - 1]);
  onTableLoadedFunctions.forEach(onloaded => onloaded());

  d3.select(container).datum(sortedUniqueTimesteps).call(timeStateComponent);
}}
"""

    def dynamic_initialize_js(self):
        controls_js = "\n".join(self.controls)
        return f"""
function(container) {{
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

  container._r2pState = {{
    refresh: function(encodedData) {{
      table = r2p.parseColumns(encodedData);
      sortedUniqueTimesteps = table["{self.i_timestep_column}"]
        .sort(d3.ascending).filter((d, i, a) => !i || d != a[i - 1]);

      onTableLoadedFunctions.forEach(onloaded => onloaded(table));

      d3.select(container).datum(sortedUniqueTimesteps).call(
        r2p.hiddenTimeState()
        .renderTimestep(t => {{
          const iTimestep = table["{self.i_timestep_column}"];

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

{controls_js}

}}
"""

    def dynamic_set_data_js(self, df):
        return f"""
function(container) {{
  container._r2pState.refresh({rows2prose.web.df_to_custom_json(df)});
}}
"""

    @classmethod
    def time_control(cls, class_name, prefix="Step"):
        return _time_control(class_name, prefix)

    @classmethod
    def position_view(cls, class_name):
        return f"""
(function() {{
  const elements = container.querySelectorAll(".{class_name}"),
        keys = elements.map(e => e.getAttribute("data-key"));

  let component;
  onTableLoadedFunctions.push(() => {{
    const [globalMin, globalMax] = d3.extent(keys, k => d3.extent(table[k])),
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
    element
      .data(keys.map(k => extractRows(table[k], iRows)))
      .call(component);
  }});
}})();
"""

    @classmethod
    def scalar_view(cls, class_name, log_scale=False):
        return f"""
(function() {{
  const element = d3.select(container).selectAll(".{class_name}"),
        keys = element.nodes().map(e => e.getAttribute("data-key"));

  let component;
  onTableLoadedFunctions.push(() => {{
    const globalMin = d3.min(keys, k => d3.min(table[k])),
          globalMax = d3.max(keys, k => d3.max(table[k])),
          min = globalMin,
          // Need a valid scale, so these need to be different.
          max = (globalMin != globalMax)
          ? globalMax
          : {"globalMax * 10" if log_scale else "globalMax + 1"};  // Visualize each point as a low value.
    component = r2p.scalarDistributionView()
      .scale(d3.{"scaleLog()" if log_scale else "scaleLinear()"}.domain([min, max]).range([0, 215]))
      {".exponentFormat(true)" if log_scale else ""}
      .height(12)
      .fontSize(13);
  }});

  renderRowsFunctions.push(function (iRows) {{
    element
      .data(keys.map(k => extractRows(table[k], iRows)))
      .call(component);
  }});
}})();
"""

    @classmethod
    def expression_view(cls, class_name, keys, text):
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


def static(df, html, script):
    element_id = str(uuid.uuid1())
    return f"""
<div id="{element_id}">{html}</div>
<script>
(function() {{
  let render = {script.static_js(df)};
  render(document.getElementById("{element_id}"));
}})();
</script>
"""


class Updater:
    def __init__(self, container_element_id, get_setdata_js):
        self.container_element_id = container_element_id
        self.get_setdata_js = get_setdata_js

    def set_data(self, df):
        return f"""
<script>
(function() {{
  let render = {self.get_setdata_js(df)};
  render(document.getElementById("{self.container_element_id}"));
}})();
</script>
"""


def dynamic(html, script):
    element_id = str(uuid.uuid1())
    s = f"""
<div id="{element_id}">{html}</div>
<script>
(function() {{
  let render = {script.dynamic_initialize_js(df)};
  render(document.getElementById("{element_id}"));
}})();
</script>
"""
    return s, Updater(element_id, script.dynamic_set_data_js)
