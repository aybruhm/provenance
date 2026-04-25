from .auth import AuthDependencies

auth_deps = AuthDependencies()
get_current_user = auth_deps.get_current_user
get_current_scope_from_apikey = auth_deps.get_current_scope_from_apikey
