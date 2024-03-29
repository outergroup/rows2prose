import * as d3 from "d3";
import { play_button_svg, pause_button_svg, restart_button_svg } from "./buttons";


const anim_t = 100;

function hiddenTimeState() {
  let renderTimestep,
      renderTime;

  function render(selection) {
    selection.selectAll(".timeState")
      .data(d => [d])
      .join(enter => {
        const timeState = enter.append("span").attr("class", "timeState");
        timeState.each(timesteps => {
          // Hack: access timeState from here, since "this" is null,
          // but we only want to run this when timeState isn't an
          // empty node.
          timeState.node()._r2pState = {
            renderedTimestep: null,
            userSelectedTimestep: null,
          };
        });
        return timeState;
      })
      .call(timeState => {
        timeState.each(sortedUniqueTimesteps => {
          let selectedTimestep = timeState.node()._r2pState.userSelectedTimestep,
              selectedIndex;
          if (selectedTimestep == null) {
            selectedIndex = sortedUniqueTimesteps.length - 1;
            selectedTimestep = sortedUniqueTimesteps[selectedIndex];
            renderTimestep(selectedTimestep);
          } else {
            selectedIndex = sortedUniqueTimesteps.indexOf(selectedTimestep);
          }
          renderTime(sortedUniqueTimesteps, selectedIndex);

          timeState.node()._r2pState.selectTimestep = function(iTimestep) {
            let state = timeState.node()._r2pState;

            const iDiscrete = Math.floor(iTimestep);

            const tTimestep = sortedUniqueTimesteps[iDiscrete];
            if (iDiscrete == sortedUniqueTimesteps.length - 1) {
              state.userSelectedTimestep = null;
            } else {
              state.userSelectedTimestep = tTimestep;
            }

            if (tTimestep != state.renderedTimestep) {
              renderTimestep(tTimestep);
              state.renderedTimestep = tTimestep;
            }

            renderTime(sortedUniqueTimesteps, iTimestep);
          };
        });
      });
  }

  render.renderTimestep = function(_) {
    if (!arguments.length) return renderTimestep;
    renderTimestep = _;
    return render;
  }

  render.renderTime = function(_) {
    if (!arguments.length) return renderTime;
    renderTime = _;
    return render;
  }

  return render;
}

function scalarView() {
  let scale = d3.scaleLinear(),
      eps = 0,
      exponentFormat = false,
      height = 30,
      fontSize = "13px",
      padRight = 30,
      tfrac = 22.5/30;

  function render(selection) {
    selection.each(function(d) {
      let x = d < 0 ? scale(d) : scale(eps);
      let rectWidth = Math.abs(scale(d) - scale(eps)),
          padding = height / 6;
      d3.select(this)
        .selectAll("svg")
        .data([d])
        .join(enter =>
          enter.append("svg")
            .attr("height", height)
            .style("vertical-align", "middle")
            .call(svg => {
              svg.append("title");

              svg.append('rect')
                .attr('y', padding)
                .attr('height', height - padding*2)
                .style('fill', "currentColor");

              svg.append('text')
                .attr('y', height * tfrac)
                .attr('fill', "currentColor")
                .style("font-size", fontSize);

              return svg;
            }))
        .call(svg => {
          svg.transition()
            .duration(anim_t)
            .ease(d3.easeLinear)
            .attr("width", scale(d) + padRight)

          svg.select("title")
            .text(d => toPrecisionThrifty(d, 5));

          svg.select('rect')
            .transition()
            .duration(anim_t)
            .ease(d3.easeLinear)
            .attr('x', x)
            .attr('width', rectWidth);

          svg.select('text')
            .text(exponentFormat ? d.toExponential(1) : toPrecisionThrifty(d, 2))
            .attr('text-anchor', d < 0 ? 'end' : 'start')
            .transition()
            .duration(anim_t)
            .ease(d3.easeLinear)
            .attr('x', d < 0 ? scale(d) - 5 : scale(eps) + rectWidth + 5);

          return svg;
        })
    });
  }

  render.scale = function(value) {
    if (!arguments.length) return scale;
    scale = value;
    return render;
  };

  render.eps = function(value) {
    if (!arguments.length) return eps;
    eps = value;
    return render;
  };

  render.exponentFormat = function(value) {
    if (!arguments.length) return exponentFormat;
    exponentFormat = value;
    return render;
  };

  render.height = function(value) {
    if (!arguments.length) return height;
    height = value;
    return render;
  };

  render.fontSize = function(value) {
    if (!arguments.length) return fontSize;
    fontSize = value;
    return render;
  };

  render.padRight = function(value) {
    if (!arguments.length) return padRight;
    padRight = value;
    return render;
  }

  render.tfrac = function(value) {
    if (!arguments.length) return tfrac;
    tfrac = value;
    return render;
  }

  return render;
}

function scalarDistributionView() {
  let scale = d3.scaleLinear(),
      exponentFormat = false,
      height = 30,
      fontSize = "13px",
      useDataMin = false,
      useDataMax = false,
      cnvMult = 4,
      pointRadius = 2.5,
      maxWidth = 300;

  let cnv_x, cnv_y, cnv_y05, cnv_y0, cnv_y1;
  function onScaleUpdate() {
    cnv_x = d3.scaleLinear()
        .domain(scale.domain())
        .range([cnvMult * scale.range()[0], cnvMult * scale.range()[1]]);
    cnv_y = d3.scaleLinear()
        .domain([0, 1])
        .range([0, cnvMult * height]);
    cnv_y05 = cnv_y(0.5);
    cnv_y0 = cnv_y(0);
    cnv_y1 = cnv_y(1);
  }

  onScaleUpdate();

  function fmin(points) {
    if (useDataMin) {
      return d3.min(points);
    } else {
      return scale.domain()[0];
    }
  }

  function fmax(points) {
    if (useDataMax) {
      return d3.max(points);
    } else {
      return scale.domain()[1];
    }
  }

  const fmintext = points => exponentFormat
        ? fmin(points).toExponential(1)
        : toPrecisionThrifty(fmin(points), 2),
        fmaxtext = points => exponentFormat
        ? fmax(points).toExponential(1)
        : toPrecisionThrifty(fmax(points), 2);

  function draw(canvasNode, div, points) {
    const min = useDataMin
      ? d3.min(points)
      : scale.domain()[0],
      max = useDataMax
      ? d3.max(points)
      : scale.domain()[1],
      width = scale(max) - scale(min);

    if (!canvasNode._r2pInitialized || (useDataMin || useDataMax)) {
      div.select(".mintext")
      // If this text is rapidly animating, the varying precision to
      // toPrecisionThrifty causes too much flickering.
        .text(useDataMin ? min.toPrecision(2)
                         : toPrecisionThrifty(min, 2));
      div.select(".maxtext")
        .text(useDataMax ? max.toPrecision(2)
                         : toPrecisionThrifty(max, 2));
      div.select(".canvasContainer")
        .style("width", `${width}px`);
      canvasNode._r2pInitialized = true;
    }

    let ctx = canvasNode.getContext("2d");
    ctx.clearRect(0, 0, canvasNode.width, canvasNode.height)
    ctx.fillStyle = "blue";
    ctx.globalAlpha = 0.4;
    ctx.lineWidth = 0;
    for (let i = 0; i < points.length; i++) {
      ctx.beginPath();
      ctx.arc(cnv_x(points[i]), cnv_y05, pointRadius*cnvMult, 0, 2 * Math.PI);
      ctx.fill();
    }
  }

  function render(selection) {
    selection.selectAll(".visualization")
      .data(d => [d])
      .join(enter => enter.append("div")
            .attr("class", "visualization")
            .style("position", "relative")
            .style("vertical-align", "middle")
            .style("display", "inline-block")
            .style("padding-right", "12px")
            .call(div => {
              div.append('span')
                .attr("class", "mintext")
                .style("font-size", fontSize)
                .style("color", "gray")
                .style("position", "relative")
                .style("top", "-1px")
                // .style("vertical-align", "text-bottom")
                .text(fmintext);

              div.append("div")
                .attr("class", "canvasContainer")
                .style("display", "inline-block")
                .style("position", "relative")
                .style("overflow", "hidden")
                .style("left", "4px")
                .style("height", `${height}px`)
                .style("border-left", "2px solid gray")
                .style("border-right", "2px solid gray")
                .style("background-color", "silver")
                .append("canvas")
                .attr("height", cnvMult * height)
                .style("height", `${height}px`)
                .attr("width", cnvMult * maxWidth)
                .style("width", `${maxWidth}px`)
                .style("vertical-align", "top");

              div.append('span')
                .attr("class", "maxtext")
                .style("font-size", fontSize)
                .style("color", "gray")
                .style("position", "relative")
                .style("left", "8px")
                .style("top", "-1px")
                // .style("vertical-align", "text-bottom")
                .text(fmaxtext);
            }))
      .call(div => {
        div.each(function(points) {
          const div = d3.select(this),
                canvas = div.select(".canvasContainer").select("canvas");
          if (this._r2pPrevPoints) {
            const interpolator = d3.interpolateNumberArray(this._r2pPrevPoints, points);

            let timer = d3.timer((elapsed) => {
              const t = Math.min(1, d3.easeCubic(elapsed / anim_t));
              draw(canvas.node(), div, interpolator(t));
              if (t === 1) {
                timer.stop();
              }
            });

          } else {
            draw(canvas.node(), div, points);
          }

          this._r2pPrevPoints = points;

        });
      });
  }

  render.scale = function(value) {
    if (!arguments.length) return scale;
    scale = value;
    onScaleUpdate();
    return render;
  };

  render.useDataMin = function(value) {
    if (!arguments.length) return useDataMin;
    useDataMin = value;
    return render;
  };

  render.useDataMax = function(value) {
    if (!arguments.length) return useDataMax;
    useDataMax = value;
    return render;
  };

  render.exponentFormat = function(value) {
    if (!arguments.length) return exponentFormat;
    exponentFormat = value;
    return render;
  };

  render.height = function(value) {
    if (!arguments.length) return height;
    height = value;
    onScaleUpdate();
    return render;
  };

  render.fontSize = function(value) {
    if (!arguments.length) return fontSize;
    fontSize = value;
    return render;
  };

  return render;
}

function toPrecisionThrifty(d, precision) {
  // If greater than 1, don't use scientific notation.
  if (d >= 1.0 && (Math.log10(d) + 1) >= precision) {
    return Math.round(d).toFixed(0);
  }

  const fullPrecision = d.toPrecision(precision),
        parsedPrecise = parseFloat(fullPrecision);

  for (let i = 1; i < precision; i++) {
    const candidate = d.toPrecision(i);
    if (parseFloat(candidate) == parsedPrecise) {
      return candidate;
    }
  }

  return fullPrecision;
}

function scalarDistributionListView() {
  let scale = d3.scaleLinear(),
      exponentFormat = false,
      fontSize = "13px",
      height = 13,
      pointRadius = 1,
      useDataMin = false,
      useDataMax = false,
      cnvMult = 4;

  function render(selection) {
    const fmin = useDataMin
          ? d => d.min
          : _ => scale.domain()[0],
          fmax = useDataMax
          ? d => d.max
          : _ => scale.domain()[1],
          fxmax = d => scale(fmax(d)),
          fxmin = d => scale(fmin(d)),
          fwidth = d => fxmax(d) - fxmin(d),
          fmintext = d => exponentFormat
          ? fmin(d).toExponential(1)
          : toPrecisionThrifty(fmin(d), 2),
          fmaxtext = d => exponentFormat
          ? fmax(d).toExponential(1)
          : toPrecisionThrifty(fmax(d), 2);

    selection.selectAll(".visualizationContainer")
      .data(d => [d])
      .join(enter => enter.append("div")
            .attr("class", "visualizationContainer")
            .style("display", "inline-block")
            .style("vertical-align", "middle")
            .style("border", "1px solid black")
            .style("border-radius", "3px")
            .style("padding-left", "5px")
            .style("padding-right", "12px")
            .style("margin-top", "1px")
            .style("margin-bottom", "1px")
            .call(div => {
              div.append('span')
                .attr('class', 'min-text')
                .style("font-size", fontSize)
                .style("color", "gray")
                .style("position", "relative")
                .style("top", d => `-${height / 2 - 5}px`)
                .text(fmintext);

              div.append("canvas")
                .style("position", "relative")
                .style("left", "4px");

              div.append('span')
                .attr('class', 'max-text')
                .style("font-size", fontSize)
                .style("color", "gray")
                .style("position", "relative")
                .style("top", d => `-${height / 2 - 5}px`)
                .style("left", "8px")
                .text(fmaxtext);
            }))
      .call(div => {
        div.style("height", `${height}px`);

        if (useDataMin) {
          div.select(".min-text")
            .text(fmintext);
        }

        if (useDataMax) {
          div.select(".max-text")
            .text(fmaxtext);
        }

        let canvas = div.select("canvas")
          .attr("width", d => cnvMult * (fwidth(d) + 2))
          .attr("height", cnvMult * height)
          .style("width", d => `${fwidth(d) + 2}px`)
          .style("height", `${height}px`);

        canvas.each(function(d) {
          let ctx = this.getContext("2d");

          const cnv_x = d3.scaleLinear()
                .domain(scale.domain())
                .range([cnvMult * (1 + scale.range()[0]), cnvMult * (scale.range()[1] + 1)]),
                cnv_y = d3.scaleLinear()
                .domain([0, d.nConfigs])
                .range([0, cnvMult * height]);

          // draw silver rect
          ctx.fillStyle = "silver";
          ctx.fillRect(0, 0, cnvMult * fwidth(d), cnvMult * height);

          ctx.strokeStyle = "gray";
          ctx.lineWidth = 2 * cnvMult;

          ctx.beginPath();
          ctx.moveTo(cnv_x(fmin(d)), cnv_y(0));
          ctx.lineTo(cnv_x(fmin(d)), cnv_y(d.nConfigs));
          ctx.stroke();

          ctx.beginPath();
          ctx.moveTo(cnv_x(fmax(d)), cnv_y(0));
          ctx.lineTo(cnv_x(fmax(d)), cnv_y(d.nConfigs));
          ctx.stroke();

          ctx.fillStyle = "blue";
          ctx.globalAlpha = 0.4;

          for (let i = 0; i < d.values.length; i++) {
            ctx.beginPath();
            ctx.arc(cnv_x(d.values[i]), cnv_y(d.iConfigs[i] + 0.5),
                    pointRadius*cnvMult, 0, 2 * Math.PI);
            ctx.fill();
          }
        });
      });
  }

  render.scale = function(value) {
    if (!arguments.length) return scale;
    scale = value;
    return render;
  };

  render.useDataMin = function(value) {
    if (!arguments.length) return useDataMin;
    useDataMin = value;
    return render;
  };

  render.useDataMax = function(value) {
    if (!arguments.length) return useDataMax;
    useDataMax = value;
    return render;
  };

  render.exponentFormat = function(value) {
    if (!arguments.length) return exponentFormat;
    exponentFormat = value;
    return render;
  };

  render.height = function(value) {
    if (!arguments.length) return height;
    height = value;
    return render;
  };

  render.pointRadius = function(value) {
    if (!arguments.length) return pointRadius;
    pointRadius = value;
    return render;
  };

  render.fontSize = function(value) {
    if (!arguments.length) return fontSize;
    fontSize = value;
    return render;
  };

  return render;
}


function positionView() {
  let scale = d3.scaleLinear();

  function render(selection) {
    selection.each(function(d) {
      d3.select(this).selectAll("svg")
        .data([d])
        .join(enter => {
          let svg = enter.append("svg")
              .attr('width', 400)
              .attr('height', 50)
              .style("vertical-align", "middle");

          // Add horizontal number line
          svg.append('line')
            .attr('x1', scale.range()[0])
            .attr('y1', 25)
            .attr('x2', scale.range()[1])
            .attr('y2', 25)
            .style('stroke', 'gray')
            .style('stroke-width', 2);

          // Add xticks
          scale.ticks(5).forEach(d => {
            svg.append('line')
              .attr('x1', scale(d))
              .attr('y1', 20)
              .attr('x2', scale(d))
              .attr('y2', 30)
              .style('stroke', 'gray')
              .style('stroke-width', 2);

            svg.append('text')
              .attr('x', scale(d))
              .attr('y', 50)
              .attr('fill', 'gray')
              .attr('text-anchor', 'middle')
              .text(d.toPrecision(2));
          });

          svg.append('g')
            .attr("class", "position")
            .call(position => {
              position.append("line")
                .attr('y1', 16)
                .attr('y2', 34)
                .style('stroke', 'currentColor')
                .style('stroke-width', 6);
              position.append("text")
                .attr("class", "position-label")
                .attr('y', 10)
                .attr('fill', 'currentColor')
                .style("text-anchor", 'middle')
                .style("font-size", "13px");
            });

          svg.append('title');
          return enter;
        })
        .call(svg => {
          svg.select(".position")
            .call(position => {
              position.transition()
                .duration(anim_t)
                .ease(d3.easeLinear)
                .attr('transform', d => `translate(${scale(d)},0)`)
            })
            .select(".position-label")
            .text(d => d.toPrecision(2));
;
          svg.select("title")
            .text(d => d.toPrecision(8));

          return svg;
        })

    });
  }

  render.scale = function(value) {
    if (!arguments.length) return scale;
    scale = value;
    return render;
  };

  return render;
}

function mixingWeightView() {
  let scale = d3.scaleLinear()
      .domain([0, 1])
      .range([0, 100]);

  function my(selection) {
    selection.selectAll("svg")
      .data(d => [d])
      .join(enter =>
        enter.append("svg")
          .attr("width", 100)
          .attr("height", 10)
          .call(svg => {
            let g = svg.append("g");

            g.append("rect")
              .attr("x", 0)
              .attr("y", 3)
              .attr("width", 100)
              .attr("height", 6)
              .attr("fill", "transparent")
              .attr("stroke", "currentColor");

            g.append("rect")
              .attr("class", "value")
              .attr("x", 0)
              .attr("y", 3)
              .attr("height", 6)
              .attr("fill", 'currentColor');

            g.append("title");

            return svg;
          }))
      .select("g")
      .call(g => {
        g.select("title")
          .text(d => d.toPrecision(5));

        g.select("rect.value")
          .transition()
          .duration(anim_t)
          .ease(d3.easeLinear)
          .attr("width", d => scale(d));
      });
  }

  my.scale = function(_) {
    if (!arguments.length) return scale;
    scale = _;
    return my;
  };

  return my;
}

function timeControl() {
  let onupdate,
      prefix = "Step";

  const padding = {top: 20, right: 0, left: 8, bottom: 10},
        msPerStep = 200;

  function renderValue(selection) {
    const slider_container = selection.select(".slider_container_container")
          .select(".slider_container");

    slider_container.select(".slider")
      .property("value", d => d.index);
    slider_container.select(".slider_text")
      .style("left", d => {
        const pctScale = d3.scaleLinear()
              .domain([0, d.sortedUniqueTimesteps.length - 1])
              .range([0, 100]),
              pxScale = d3.scaleLinear()
              .domain([0, d.sortedUniqueTimesteps.length - 1])
              .range([-30, -45]);
        return `calc(${pctScale(d.index)}% + ${pxScale(d.index)}px)`;
      })
      .text(d => {
        const stepLabel = d.sortedUniqueTimesteps[Math.floor(d.index)];
        return `${prefix} ${stepLabel}`;
      });
  }

  function render(selection) {
    selection.each(function(d) {

      // Create a slider for selecting the current timestep

      const container = d3.select(this);

      d3.select(this).selectAll(".slider_container_container")
        .data([d])
        .join(enter => {
          const slider_container_container = enter.append("div")
                .attr("class", "slider_container_container"),
                slider_container = slider_container_container.append("div")
                .attr("class", "slider_container")
                .style("display", "inline-block")
                .style("width", `calc(100% - ${25 + padding.left}px)`)
                .style("position", "relative")
                .style("margin", `${padding.top}px ${padding.right}px ${padding.bottom}px ${padding.left}px`);

          const slider_ = slider_container.append("input")
                .attr("class", "slider")
                .style("display", "inline")
                .attr("type", "range")
                .attr("id", "timestep")
                .attr("step", "any")
                .style("width", "100%")
                .style("vertical-align", "text-bottom");

          slider_container.append("span")
            .attr("class", "slider_text")
            .style("position", "absolute")
            .style("top", "-20px")
            .style("width", "80px")  // avoid text wrapping when it's near an edge
            .style("text-align", "center");

          slider_container_container.each(function(d) {
            const slider_container_container = d3.select(this),
                  slider_ = slider_container_container
                  .select(".slider_container")
                  .select(".slider");

            /**
             * Slider logic
             */
            (function() {
              // This is per instance state that should only be created
              // on enter. Thus it needs to run inside of enter.each.
              let stopped = true,
                  pointer_down = false,
                  vStart;

              function restart() {
                slider_.node().value = 1;
                play();
              }

              function getMax() {
                return parseInt(slider_.node().getAttribute("max"));
              }

              function set_stopped_button() {
                pause_button.style("display", "none");
                if (slider_.node().value == getMax()) {
                  play_button.style("display", "none");
                  restart_button.style("display", "inline");
                } else {
                  play_button.style("display", "inline");
                  restart_button.style("display", "none");
                }
              }

              function set_playing_button() {
                play_button.style("display", "none");
                if (slider_.node().value == getMax()) {
                  pause_button.style("display", "none");
                  restart_button.style("display", "inline");
                } else {
                  pause_button.style("display", "inline");
                  restart_button.style("display", "none");
                }
              }

              function pause() {
                stopped = true;
              }

              function play() {
                vStart = parseFloat(slider_.node().value);

                if (vStart >= getMax()) {
                  vStart = getMax();
                  stopped = true;
                } else {
                  stopped = false;
                }

                if (!stopped) {
                  let timer = d3.timer((elapsed) => {
                    if (!stopped && !pointer_down) {
                      let value = vStart + elapsed / msPerStep;
  
                      if (value >= getMax()) {
                        value = getMax();
                        stopped = true;
                      }
  
                      let d = selection.datum();
                      d.index = value;
                      renderValue(selection.datum(d))
                      slider_.node()._vp_onupdate(value);
                    }
  
                    if (stopped) {
                      set_stopped_button();
                    }
  
                    if (stopped || pointer_down) {
                      timer.stop();
                    }
                  });

                  play_button.style("display", "none");
                  pause_button.style("display", "inline");
                  restart_button.style("display", "none");
                }
              }

              let play_button = slider_container_container.append("span")
                  .style("display", "none")
                  .style("vertical-align", "middle")
                  .style("margin-left", "10px")
                  .on("click", play)
                  .html(play_button_svg),
                  pause_button = slider_container_container.append("span")
                  .style("display", "none")
                  .style("vertical-align", "middle")
                  .style("margin-left", "8px")
                  .on("click", pause)
                  .html(pause_button_svg),
                  restart_button = slider_container_container.append("span")
                  .style("display", "inline")
                  .style("vertical-align", "middle")
                  .style("margin-left", "8px")
                  .on("click", restart)
                  .html(restart_button_svg);

              slider_
                .on("input", () => {
                  let v = parseFloat(slider_.node().value);
                  if (v >= getMax()) {
                    v = getMax();
                    stopped = true;
                  }

                  if (stopped) {
                    set_stopped_button();
                  } else {
                    vStart = parseFloat(slider_.node().value);
                    play();
                    set_playing_button();
                  }
                  slider_.node()._vp_onupdate(v);

                  let d = selection.datum();
                  d.index = v;
                  renderValue(selection.datum(d))
                })
                .on("pointerdown", () => {
                  pointer_down = true;
                })
                .on("pointerup", () => {
                  pointer_down = false;
                  if (!stopped) play();
                });
            })();
          });

          return slider_container_container;
        })
        .call(slider_container_container => {
          const slider_container = slider_container_container.select(".slider_container"),
                slider_ = slider_container.select(".slider");

          slider_
            .attr("min", d => 0)
            .attr("max", d => d.sortedUniqueTimesteps.length - 1);

          slider_.node()._vp_onupdate = onupdate;
          renderValue(selection);
        });
    });
  }

  render.onupdate = function(_) {
    if (!arguments.length) return onupdate;
    onupdate = _;
    return render;
  };

  render.prefix = function(_) {
    if (!arguments.length) return prefix;
    prefix = _;
    return render;
  };

  return render;
}

export {
  hiddenTimeState,
  positionView,
  scalarDistributionListView,
  scalarDistributionView,
  scalarView,
  timeControl,
};
