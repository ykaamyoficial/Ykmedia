import { z } from "zod";

export const nonEmptyString = z.string().trim().min(1, "Campo obrigatorio.");
