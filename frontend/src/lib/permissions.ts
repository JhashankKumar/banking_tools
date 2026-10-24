export type Role = "analyst" | "supervisor" | "auditor";

export interface NavItem {
  href: string;
  label: string;
}

/** Navigation mirrors the API's role permissions; the API remains the enforcement point. */
export function navItemsFor(role: Role): NavItem[] {
  switch (role) {
    case "analyst":
      return [
        { href: "/alerts", label: "Alerts" },
        { href: "/cases", label: "Cases" },
      ];
    case "supervisor":
      return [
        { href: "/alerts", label: "Alerts" },
        { href: "/cases", label: "Cases" },
        { href: "/reviews", label: "Reviews" },
        { href: "/users", label: "Users" },
      ];
    case "auditor":
      return [{ href: "/audit", label: "Audit" }];
  }
}

export function landingFor(role: Role): string {
  return role === "auditor" ? "/audit" : "/alerts";
}

export const ROLE_LABEL: Record<Role, string> = {
  analyst: "Analyst",
  supervisor: "Supervisor",
  auditor: "Auditor",
};
