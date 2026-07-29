import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { UserPreferencesProvider } from "@/shared/config/user-preferences";
import { useUserPreferences } from "@/shared/config/useUserPreferences";

function PreferencesProbe() {
  const { preferences, setPreferences } = useUserPreferences();
  return (
    <button type="button" onClick={() => setPreferences({ ...preferences, density: "comfortable" })}>
      {preferences.density}
    </button>
  );
}

describe("UserPreferencesProvider", () => {
  it("stores user preferences locally", async () => {
    render(
      <UserPreferencesProvider>
        <PreferencesProbe />
      </UserPreferencesProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "compact" }));

    expect(screen.getByRole("button", { name: "comfortable" })).toBeInTheDocument();
  });
});
