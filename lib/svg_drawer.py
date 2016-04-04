import os
import math
import logging
from colour import Color


def render(template_file, content, output_file=None):
    with open(template_file, 'r') as f_template:
        output = f_template.read().format(**content)
        if output_file:
            with open(output_file, 'w') as f_output:
                f_output.write(output)
            return output
        else:
            return output


def draw_dial():
    markers = ""
    for i in range(60):
        if not i % 5:
            length = 10
        else:
            length = 5

        markers += """<g transform="rotate({}, 50, 50)">
                        <line x1="50" y1="1" x2="50" y2="{}" stroke-width=".3" stroke="black"></line>
                      </g>""".format(i * 6, length)
    return markers


def calc_path(center, idx, time, verbose=False):
    # TODO: adjust step proportionally to max(idx)
    if verbose:
        logging.debug(locals())
    step = 2
    radius = 46 - idx*step
    angle = int(time) * 2 * math.pi / 60

    if not angle:  # better avoid 0 angle to have a full circle (almost)
        angle = math.pi / 60

    if verbose:
        logging.debug("Angle {}deg".format(round(angle*180/math.pi)))
    start = (center[0], center[1] - radius)
    if verbose:
        logging.debug("Start {}".format(start))
    end = (center[0] + radius * math.sin(angle), center[1] - radius * math.cos(angle))
    if verbose:
        logging.debug("End {}".format(end))

    move = "M{} {}".format(start[0], start[1])
    # ARC A rx ry x-axis-rotation large-arc-flag sweep-flag x y
    if angle < math.pi:
        large = 1
    else:
        large = 0

    arc = "A {} {}, {}, {}, {}, {} {}".format(radius, radius, 1, large, 0, end[0], end[1])
    line = "L {} {} Z".format(center[0], center[1])

    return "{} {} {}".format(move, arc, line)


def gen_palette(start, end, steps):
    return list(Color(start).range_to(Color(end), steps + 3))


def draw_legend(text, idx, color):
    legend_template = """<text x="0" y="{legend_y}" stroke-width=".1" stroke="{color}" fill="{color}"
                             font-family="Arial" font-size="3">{text}</text>"""

    return legend_template.format(legend_y=(4*idx)+103, text=text, color=color)


def draw_next_vehicles(v, base_color="#FF0000", offset=0):
    colors = gen_palette(base_color, 'black', len(v))
    path = []
    for idx, vehicle in enumerate(v):
        path.append("""<path stroke="{color}" fill="{color}"
                                      fill-rule="evenodd"
                                      stroke-width=".1" stroke-linejoin="round"
                                      stroke-linecap="butt"
                                      d="{d}" ></path>""".format(color=colors[idx % 7],
                                                                 d=calc_path((50, 50), idx+offset, vehicle)))
    return path


def draw_groups(groups, base_colors):
    template_file = os.path.join(os.path.dirname(__file__) + '/../res/meter.svg')
    elements = []
    offset = 0
    legends = []
    for i, group in enumerate(groups):
        legends.append(draw_legend(group, i, base_colors[i]))
        logging.debug("New group {}, offset:{}".format(group, offset))
        group_res = draw_next_vehicles(groups[group], base_colors[i], offset)
        offset += len(group_res)
        elements.append("\n".join(group_res))

    data = {'vehicles_arcs': "\n".join(elements + legends), 'markers': draw_dial()}
    result = render(template_file, data)
    return result




