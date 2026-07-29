type YkAvatarProps = {
  name: string;
  imageUrl?: string;
  size?: "sm" | "md" | "lg";
  alt?: string;
};

function initials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function YkAvatar({ name, imageUrl, size = "md", alt }: YkAvatarProps) {
  const dimension = {
    sm: "h-8 w-8 text-xs",
    md: "h-9 w-9 text-sm",
    lg: "h-12 w-12 text-base",
  }[size];

  if (imageUrl) {
    return <img src={imageUrl} alt={alt ?? name} className={`${dimension} rounded-full object-cover`} />;
  }

  return (
    <div className={`${dimension} flex items-center justify-center rounded-full bg-muted font-semibold text-foreground`}>
      {initials(name) || "Y"}
    </div>
  );
}
