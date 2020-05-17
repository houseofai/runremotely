import pkg_resources
import types
import tempfile
from pipreqs import pipreqs as pi

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

        return pi.get_pkg_names(list(set(imports)))

    def get_requirements(self):
        requirements = []
        imports = self.get_imports()
        for m in pkg_resources.working_set:
            if m.project_name in imports and m.project_name!="pip":
                requirements.append((m.project_name, m.version))
        return requirements

    def get_formatted_imports(self):
        candidates = pi.get_pkg_names(self.get_imports())

        pypi_server = "https://pypi.python.org/pypi/"
        proxy = None
        local = pi.get_import_local(candidates)
        # Get packages that were not found locally
        difference = [x for x in candidates
                      if x.lower() not in [z['name'].lower() for z in local]]
        imports = local + pi.get_imports_info(difference,
                                           proxy=proxy,
                                           pypi_server=pypi_server)
        return imports

    def get_requirements_file(self):
        requirements = self.get_formatted_imports()
        fmt = '{name}=={version}'
        formatted_reqs = '\n'.join(fmt.format(**item) if item['version'] else '{name}'.format(**item) for item in requirements) + '\n'
        fd, f = tempfile.mkstemp(suffix = '.reqs')
        open(f, 'w').write(formatted_reqs)
        return f
