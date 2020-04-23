"""Wrap `cantools generate_c_source` in a macro"""

def _generate_c_impl(ctx):
    outdir = ctx.build_file_path.split('/BUILD')[0]
    all_outputs = []

    for target in ctx.attr.dbcs:
        for dbc in target.files.to_list():
            outputs = []
            args = ctx.actions.args()
    
            basename = dbc.path.split("/")[-1].split(".dbc")[0]
            outputs.append(ctx.actions.declare_file("%s.c" % basename))
            outputs.append(ctx.actions.declare_file("%s.h" % basename))

            args.add("generate_c_source")
            args.add(dbc.path)
            args.add("--outdir")
            args.add("%s/%s" % (ctx.bin_dir.path, outdir))

            for arg in ctx.attr.args:
                args.add(arg)
                if arg == "--generate-fuzzer" or arg == "-f":
                    outputs.append(ctx.actions.declare_file("%s_fuzzer.c" % basename))
                    outputs.append(ctx.actions.declare_file("%s_fuzzer.mk" % basename))

            ctx.actions.run(
                inputs = [dbc],
                outputs = outputs,
                executable = ctx.attr._cantools.files_to_run,
                arguments = [args],
                progress_message = "Generating DBC C source code for %s" % ctx.label,
            )
            all_outputs.extend(outputs)

    return [
        DefaultInfo(files = depset(all_outputs))
    ]

generate_c = rule(
    implementation = _generate_c_impl,
    attrs = {
        "dbcs": attr.label_list(
            doc = "List of filegroups that contain DBC files",
            mandatory = True,
            allow_files = True,
        ),
        "args": attr.string_list(
            doc = "Additional args to pass into cantools generate_c_source command",
            allow_empty = True,
            mandatory = False,
        ),
        "_cantools": attr.label(
            doc = "py_binary cantools target",
            executable = True,
            cfg = "host",
            default = Label("//cantools:cantools"),
        ),
    }
)
