"use client";

import { Segmented } from "@/components/ui/Segmented";
import { useTheme, type Theme } from "@/components/theme/use-theme";

export function ThemeSwitch() {
  const { theme, setTheme } = useTheme();
  return (
    <Segmented<Theme>
      label="Theme"
      value={theme}
      onChange={setTheme}
      options={[
        { value: "light", label: "☀ Light" },
        { value: "dark", label: "☾ Dark" },
      ]}
    />
  );
}
