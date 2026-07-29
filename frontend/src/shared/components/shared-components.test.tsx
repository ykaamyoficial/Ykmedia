import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { YkNoConnectionState } from "@/shared/components/empty-states";
import { YkFullscreenLoading, YkProgress } from "@/shared/components/loading";
import { YkPagination } from "@/shared/components/YkPagination";
import { YkSearchBox } from "@/shared/components/YkSearchBox";

describe("shared components", () => {
  it("renders loading and empty states", () => {
    render(
      <>
        <YkFullscreenLoading />
        <YkNoConnectionState />
      </>,
    );

    expect(screen.getByLabelText("Preparando interface")).toBeInTheDocument();
    expect(screen.getByText("Sem conexao")).toBeInTheDocument();
  });

  it("renders progress", () => {
    render(<YkProgress value={50} />);

    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "50");
  });

  it("changes pages", async () => {
    const onPageChange = vi.fn();
    render(<YkPagination page={1} pageCount={3} onPageChange={onPageChange} />);

    await userEvent.click(screen.getByRole("button", { name: /proxima/i }));

    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it("clears search", async () => {
    const onChange = vi.fn();
    render(<YkSearchBox value="abc" onChange={onChange} />);

    await userEvent.click(screen.getByRole("button", { name: /limpar busca/i }));

    expect(onChange).toHaveBeenCalledWith("");
  });
});
