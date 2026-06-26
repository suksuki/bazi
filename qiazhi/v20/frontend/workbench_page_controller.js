(function registerWorkbenchPageController(global) {
  const routes = global.QiazhiWorkbenchRoutes;
  const config = Object.freeze({
    page: document.body.dataset.workbenchPage || "auto",
    defaultMode: document.body.dataset.workbenchDefaultMode || "reading",
    lockMode: document.body.dataset.workbenchLockMode === "true",
  });

  const allowedModes = (role) => {
    const modes = routes.modesForRole(role);
    if (!config.lockMode) return modes;
    return modes.includes(config.defaultMode) ? [config.defaultMode] : ["reading"];
  };

  const routeToRolePageIfNeeded = (role) => {
    const normalized = routes.normalizeRole(role);
    const target = routes.pageForRole(role);
    const currentPath = window.location.pathname;
    if (config.page === "auto" && currentPath !== target) {
      window.location.replace(`${target}${window.location.search}`);
      return true;
    }
    const rolePage = routes.pageForRole(normalized);
    const pageRole = {
      user: "user",
      practitioner: "analyst",
      observe: "admin",
    }[config.page];
    if (config.page === "guest" && role !== "guest" && currentPath !== rolePage) {
      window.location.replace(`${rolePage}${window.location.search}`);
      return true;
    }
    if (pageRole && normalized !== pageRole && currentPath !== rolePage) {
      window.location.replace(`${rolePage}${window.location.search}`);
      return true;
    }
    if (config.lockMode && !routes.modesForRole(normalized).includes(config.defaultMode) && currentPath !== target) {
      window.location.replace(`${target}${window.location.search}`);
      return true;
    }
    return false;
  };

  const routeAnonymousIfNeeded = () => {
    if (config.page === "practitioner" || config.page === "observe") {
      window.location.replace("/v20/ui/");
      return true;
    }
    return false;
  };

  const renderNavigation = (role) => {
    const measureLink = document.querySelector('[data-ui="nav_measure"]');
    if (measureLink) measureLink.href = routes.pageForRole(role);
  };

  global.QiazhiWorkbenchPageController = Object.freeze({
    config,
    initialMode: config.defaultMode,
    normalizeRole: routes.normalizeRole,
    allowedModes,
    routeAnonymousIfNeeded,
    routeToRolePageIfNeeded,
    renderNavigation,
  });
})(window);
