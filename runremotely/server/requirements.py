import pkg_resources
import types
import tempfile

class Requirements():
    def __init__(self, context):
        self.context = context

    def get_imports(self):
        imports = []
        for name, val in self.context.items():
            if isinstance(val, types.ModuleType):
                imports.append(val.__name__.split(".")[0])
            elif isinstance(val, type):
                imports.append(val.__module__.split(".")[0])

        return list(set(imports))

    def get_requirements(self):
        requirements = []
        imports = self.get_imports()
        for m in pkg_resources.working_set:
            if m.project_name in imports and m.project_name!="pip":
                requirements.append((m.project_name, m.version))
        return requirements

    def get_requirements_file(self):
        requirements = self.get_requirements()
        reqlines = ""
        for r in requirements:
            reqlines += "{}=={}\n".format(*r)

        fd, f = tempfile.mkstemp(suffix = '.reqs')
        open(f, 'w').write(reqlines)
        return f
