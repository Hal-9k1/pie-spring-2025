import sys
import os
import textwrap

class ModuleInfo:
    __slots__ = "name", "func_call", "file_path", "body_text"
    def __init__(self, name, func_call, file_path, body):
        self.name = name
        self.func_call = func_call
        self.file_path = file_path
        self.body_text = body

def file_path_from_basename(file_path, rel_file_path):
    if os.path.isfile(file_path + ".py"):
        # it's a module
        return file_path + ".py"
    if os.path.isfile(os.path.join(file_path, "__init__.py")):
        # it's a package
        return os.path.join(file_path, "__init__.py")
    # doesn't exist
    return None

def escape_module_name(name):
    return name.replace("_", "__").replace(".", "_")

def unescape_module_name(name):
    return '_'.join(segment.replace("_", ".") for segment in name.split("__"))

def trim_common_module_segments(module, compare_against):
    common_strlen = 0
    for segments in zip(unescape_module_name(module).split("_"),
        unescape_module_name(compare_against).split("_")):
        if segments[0] == segments[1]:
            common_strlen += 1 + len(segments[0])
        else:
            break
    return module[common_strlen:]

def process_file(file_path, indent=" " * 4, module_name=None, module_list=None, import_cursor=0,
        auto_detect_entry_points=True):
    """Preprocesses a python script by recursively transcluding imported files."""

    if module_list == None:
        module_list = []
        is_top_level = True
        entry_point_line_nums = []
    else:
        is_top_level = False
        if any(module_info.name == module_name for module_info in module_list):
            raise RuntimeError(f"Detected cyclic import of module {module_name}.")
    with open(file_path, "r", encoding="utf-8") as file:
        module_buffer = []
        while True:
            line = file.readline()
            if not line:
                break
            words = line.strip().split(" ")
            if not len(words):
                module_buffer.append(line)
            elif words[0] == "import" or words[0] == "from":
                imported_module_raw_name = words[1]
                path_segments = imported_module_raw_name.split(".")
                imported_module_name = escape_module_name(imported_module_raw_name)
                prev_imported_module = next((module for module in module_list
                    if module.name == imported_module_name
                    or (module_name and trim_common_module_segments(module.name, module_name) ==
                    imported_module_name)), None)
                module_exports = f"_HELPER_module_export_dict['{imported_module_name}']"
                import_file_path = file_path_from_basename(os.path.join(*path_segments), module_name)
                if prev_imported_module:
                    func_call = prev_imported_module.func_call
                elif not import_file_path:
                    # module not found. assume it's built in and leave the import statement intact
                    module_buffer.append(line)
                    continue
                else:
                    imported_body_text = process_file(import_file_path,
                        indent=indent, module_name=imported_module_name, module_list=module_list,
                        import_cursor=import_cursor + 1)
                    func_call = f"_HELPER_import_{imported_module_name}()"
                    imported_module_buffer = [
                        f"def {func_call}:",
                        f"{indent}if '{imported_module_name}' in _HELPER_module_export_dict:",
                        f"{indent * 2}return",
                        f"{indent}__name__ = '{imported_module_raw_name}'",
                        "",
                        f"{indent}# Begin imported file."
                    ]
                    imported_module_buffer.extend([indent + line for line in imported_body_text.splitlines()])
                    imported_module_buffer.append(
                        f"\n{indent}# End imported file.\n"
                        f"{indent}{module_exports} = locals()\n\n\n"
                    )
                if words[0] == "import" and (len(words) < 3 or words[2] != "as"):
                    import_mode = "import"
                    after_import_word_idx = 2
                elif words[0] == "import":
                    import_mode = "import as"
                    after_import_word_idx = 4
                elif words[0] == "from" and (len(words) < 5 or words[4] != "as"):
                    import_mode = "from import"
                    after_import_word_idx = 4
                elif words[0] == "from":
                    import_mode = "from import as"
                    after_import_word_idx = 6
                else:
                    raise RuntimeError("Typo?")
                #import_only_line = " ".join(line.strip().split(" ")[:after_import_word_idx])
                import_line = f"{func_call}; "
                if import_mode == "import":
                    module_segments = imported_module_raw_name.split(".")
                    for i in range(len(module_segments)):
                       module_partial = ".".join(module_segments[:i + 1])
                       module_partial_escaped = escape_module_name(module_partial)
                       import_line += f"{module_partial} = _HELPER_Module('{module_partial_escaped}'); "
                    #import_line += f"{imported_module_raw_name} = _HELPER_Module('{imported_module_name}')"
                elif import_mode == "import as":
                    import_line += f"{words[3]} = _HELPER_Module('{imported_module_name}')"
                elif import_mode == "from import":
                    if words[3] == "*":
                        import_line += f"exec(\"[exec(k + ' = v') for k, v in {module_exports}.items() if not k.startswith('__')]\")"
                    else:
                        import_line += f"{words[3]} = {module_exports}[\"{words[3]}\"]"
                elif import_mode == "from import as":
                    import_line += f"{words[5]} = {module_exports}[\"{words[3]}\"]"
                else:
                    raise RuntimeError("Typo?")
                import_line += " # " + line.strip() + "\n"
                module_buffer.append(import_line)

                if not prev_imported_module:
                    module_list.insert(import_cursor, ModuleInfo(imported_module_name, func_call,
                        import_file_path, "\n".join(imported_module_buffer)))
            elif not auto_detect_entry_points and words[0] == "@_PREP_ENTRY_POINT":
                module_buffer.append(line[:line.find("@")] + "@_HELPER_entry_point\n")
                entry_point_line_nums.append(len(module_buffer))
            else:
                if auto_detect_entry_points and words[0] == "def" and is_top_level:
                    module_buffer.append(line[:line.find("d")] + "@_HELPER_entry_point\n")
                    entry_point_line_nums.append(len(module_buffer))
                module_buffer.append(line)
        if is_top_level:
            strings = [
                f"_HELPER_module_export_dict = {{}}",
                f"_HELPER_entry_point_line_nums = [{', '.join(str(num) for num in entry_point_line_nums)}]",
                f"class _HELPER_Module:",
                f"{indent}def __init__(self, module_name):",
                f"{indent * 2}self.__dict__ = _HELPER_module_export_dict[module_name] if module_name and module_name in _HELPER_module_export_dict else dict()",
                f"{indent}def __getitem__(self, key):",
                f"{indent * 2}return self.__dict__[key]",
                f"{indent}def __setitem__(self, key, value):",
                f"{indent * 2}self.__dict__[key] = value",
                f"def _HELPER_entry_point(func):",
                f"{indent}import functools",
                f"{indent}@functools.wraps(func)",
                f"{indent}def wrapped(*args, **kwargs):",
                f"{indent * 2}try:",
                f"{indent * 3}return func(*args, **kwargs)",
                f"{indent * 2}except Exception as e:",
                f"{indent * 3}print('Source traceback (most recent call last):')",
                f"{indent * 3}frame_lines = []",
                f"{indent * 3}tb = e.__traceback__",
                f"{indent * 3}while tb:",
                f"{indent * 4}translation_result = _HELPER_translate_line_no(tb.tb_lineno)",
                f"{indent * 4}if not translation_result:",
                f"{indent * 5}tb = tb.tb_next",
                f"{indent * 5}continue",
                f"{indent * 4}module_path, line_no = translation_result",
                f"{indent * 4}frame_lines.append(f'  File \"{{module_path}}\", line {{line_no}}, in {{tb.tb_frame.f_code.co_name}}')",
                f"{indent * 4}tb = tb.tb_next",
                f"{indent * 3}print('\\n'.join(frame_lines))",
                f"{indent * 3}print(type(e).__name__ + (': ' if str(e) else '') + str(e))",
                f"{indent * 3}exit(1)",
                f"{indent}return wrapped",
                f"def _HELPER_translate_line_no(line_no):",
            ]
            strings = [string + "\n" for string in strings]
            running_line_num = len(strings) + 10 + 2 * len(module_list) # two lines added per module
            module_line_entries = []
            for module in module_list:
                module_line_entries.append(
                    f"{indent}elif line_no >= {running_line_num + 5}:\n"
                    f"{indent * 2}return '{module.file_path}', line_no - {running_line_num + 4}\n"
                )
                running_line_num += module.body_text.count("\n")
            module_line_entries.append(
                f"{indent}if line_no >= {running_line_num}:\n"
                f"{indent * 2}skipped_lines = 0\n"
                f"{indent * 2}for entry_point_line_num in _HELPER_entry_point_line_nums:\n"
                f"{indent * 3}if entry_point_line_num + {running_line_num} <= line_no:\n"
                f"{indent * 4}skipped_lines += 1\n"
                f"{indent * 3}else:\n"
                f"{indent * 4}break\n"
                f"{indent * 2}return '{''.join(os.path.basename(file_path).split('.')[:-1])}', line_no - {running_line_num} - skipped_lines\n"
            )
            strings.extend(reversed(module_line_entries))
            strings.extend(module.body_text for module in module_list)
            strings.append("# End imports.\n")
            strings.extend(module_buffer)
            return ("".join(strings), module_list)
        else:
            return "".join(module_buffer)

if __name__ == "__main__":
    if "--help" in sys.argv:
        # underline/bold/end style underline ansi escape codes
        ul = "\u001b[4m" if sys.stdout.isatty() else ""
        bd = "\u001b[1m" if sys.stdout.isatty() else ""
        es = "\u001b[0m" if sys.stdout.isatty() else ""
        print(f"{bd}{sys.argv[0]}{es}: {process_file.__doc__}", file=sys.stderr)
        print(file=sys.stderr)
        print("Synopsis:", file=sys.stderr)
        print(
            f"  {bd}{sys.argv[0]}{es} {ul}entryfile{es} "
            f"[{bd}--build-file={es}{ul}buildfile{es}] [{bd}--auto-detect-entry-points{es}]",
            file=sys.stderr)
        print(
            f"  {bd}{sys.argv[0]}{es} {ul}entryfile{es} "
            f"{bd}--dependency-file={es}{ul}depfile{es} {bd}--build-file={es}{ul}buildfile{es}",
            file=sys.stderr)
        print(
            f"  {bd}{sys.argv[0]} --help{es}",
            file=sys.stderr)
        print(file=sys.stderr)
        print(textwrap.fill(
            f"Writes to {ul}buildfile{es} (or standard output if unspecified) a single Python "
            f"script containing the contents of {ul}entryfile{es} and all its imported "
            f"non-builtin modules, which can be run independently. If "
            f"{bd}--auto-detect-entry-points{es} is set, function definitions in "
            f"{ul}entryfile{es} will be wrapped with error-handling code that preserves original "
            f"file names in stack traces. This may cause inaccuracies if functions in "
            f"{ul}entryfile{es} call each other. If not set, only functions annotated with "
            f"'@_PREP_ENTRY_POINT' in {ul}entryfile{es} will be wrapped with this handling code."),
            file=sys.stderr)
        print(file=sys.stderr)
        print(textwrap.fill(
            f"If {bd}--dependency-file{es} is specified, the preprocessed file is not output. "
            f"Instead, Makefile rules are written to {ul}depfile{es} that rebuild "
            f"{ul}buildfile{es} (which must be specified in this form of the command) and "
            f"{ul}depfile{es} when imported files are changed."),
            file=sys.stderr)
        print(file=sys.stderr)
        print(textwrap.fill(
            f"If an imported file cannot be found, it is treated as a builtin Python module and "
            f"the import statement is left intact in the preprocessed output and omitted from "
            f"the Makefile rule dependencies. Importing comma-separated names from modules using "
            f"the '{bd}from{es} {ul}module{es} {bd}import{es} {ul}name{es}, ... ' syntax is not "
            f"supported."),
            file=sys.stderr)
        print(file=sys.stderr)
        print(textwrap.fill(
            f"Imports from packages are supported, but all imports will be resolved from the "
            f"current directory; relative imports are not supported."),
            file=sys.stderr)
        exit(0)
    output, modules = process_file(sys.argv[1],
        auto_detect_entry_points="--auto-detect-entry-points" in sys.argv)
    depfile_opt = "--dependency-file="
    # Use last duplicate option:
    dep_fn = next((arg[len(depfile_opt):] for arg in reversed(sys.argv)
        if arg.startswith(depfile_opt)), None)
    build_fn_opt = "--build-file="
    build_fn = next((arg[len(build_fn_opt):] for arg in reversed(sys.argv)
        if arg.startswith(build_fn_opt)), None)
    if dep_fn:
        if not build_fn:
            print("--build-file must be specified if writing dependencies.", file=sys.stderr)
            exit(1)
        # Include both entry file and this preprocessor as dependencies:
        dep_paths = [module.file_path for module in modules] + sys.argv[:2]
        deps = '\\\n  '.join(f"./{path} " for path in dep_paths)
        with open(dep_fn, "w") as output_file:
            print(f"{build_fn}: {deps}", file=output_file)
            print(f"\tpython {sys.argv[0]} {sys.argv[1]} --build-file={build_fn}",
                file=output_file)
            print(f"{dep_fn}: $(filter $(shell find -name \"*.py\" -not -path \"./.*\"),{deps})",
                file=output_file)
            print((f"\tpython {sys.argv[0]} {sys.argv[1]} --dependency-file={dep_fn} "
                f"--build-file={build_fn}"),
                file=output_file)
    else:
        try:
            build_file = open(build_fn, "w") if build_fn else sys.stdout
            print(output, file=build_file)
        except Exception as e:
            build_file.close()
            raise e
