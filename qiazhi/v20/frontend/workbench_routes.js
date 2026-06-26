(function registerWorkbenchRoutes(global) {
  const USER_PAGE = "/v20/ui/workbench-user.html";
  const GUEST_PAGE = "/v20/ui/workbench-guest.html";
  const PRACTITIONER_PAGE = "/v20/ui/workbench-practitioner.html";
  const OBSERVE_PAGE = "/v20/ui/workbench-observe.html";

  const normalizeRole = (role) => {
    if (role === "guest") return "guest";
    if (role === "admin") return "admin";
    if (role === "lab") return "lab";
    if (role === "analyst") return "analyst";
    return "user";
  };

  const pageForRole = (role) => {
    if (role === "guest") return GUEST_PAGE;
    const normalized = normalizeRole(role);
    if (normalized === "admin") return OBSERVE_PAGE;
    if (normalized === "lab") return OBSERVE_PAGE;
    if (normalized === "analyst") return PRACTITIONER_PAGE;
    return USER_PAGE;
  };

  const modesForRole = (role) => {
    const normalized = normalizeRole(role);
    if (normalized === "guest") return ["reading"];
    if (normalized === "admin") return ["reading", "practitioner", "observe"];
    if (normalized === "lab") return ["reading", "observe"];
    if (normalized === "analyst") return ["reading", "practitioner"];
    return ["reading"];
  };

  global.QiazhiWorkbenchRoutes = Object.freeze({
    normalizeRole,
    pageForRole,
    modesForRole,
  });
})(window);
