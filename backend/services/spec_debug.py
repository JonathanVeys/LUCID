
def get_chart_type(chart):
    '''
    
    '''
    vega_lite = chart["vega_lite"]
    return str(vega_lite["mark"]["type"]) if vega_lite.get("projection") else str(vega_lite["mark"])
    


def print_spec_info(spec):
    '''
    
    '''
    lines: list[str] = []
    if spec.get("vis_spec"):
        vis_spec = spec['vis_spec']
        #Gather metadata about the vis_spec
        lines.append("Spec Metadata:")
        for label, key in (
            ("Title", "title"),
            ("Description", "description"),
            ("Layout Mode", "layout_mode")
        ):
            lines.append(f"      -{label}: {vis_spec[key]}")
        lines.append(f"      -Num of charts: {len(vis_spec["charts"])}")

        #Gather chart specific metadata
        for i,chart in enumerate(vis_spec["charts"]):
            lines.append(f"Chart {i+1} Metadata:")
            for label, key in (
                ("Chart Role", "role"),
                ("Chart Title", "title"),
                ("Chart SQL", "sql")
            ):
                lines.append(f"      -{label}: {chart[key]}")
            lines.append(f"      -Chart Type: {get_chart_type(chart)}")

    else:
        lines.append(f"Answarable: {spec["answerable"]}")
        lines.append(f"Reason: {spec["reason"]}")

    print("\n".join(lines))