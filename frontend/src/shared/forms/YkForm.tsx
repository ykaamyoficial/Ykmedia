import { type FormEvent, type ReactNode } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  type DefaultValues,
  type FieldValues,
  FormProvider,
  type SubmitHandler,
  useForm,
} from "react-hook-form";
import { type ZodType } from "zod";

type YkFormProps<TValues extends FieldValues> = {
  schema?: ZodType<TValues>;
  defaultValues: TValues;
  onSubmit: SubmitHandler<TValues>;
  children: ReactNode;
};

export function YkForm<TValues extends FieldValues>({
  schema,
  defaultValues,
  onSubmit,
  children,
}: YkFormProps<TValues>) {
  const form = useForm<TValues>({
    defaultValues: defaultValues as DefaultValues<TValues>,
    resolver: schema ? zodResolver(schema) : undefined,
  });
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    void form.handleSubmit(onSubmit)(event);
  };

  return (
    <FormProvider {...form}>
      <form onSubmit={handleSubmit}>{children}</form>
    </FormProvider>
  );
}
