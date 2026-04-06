import { Profile } from "@/types/profile";

export function getProfileDisplayName(
  profile: Pick<Profile, "username" | "first_name" | "last_name">,
): string {
  const fullName = [profile.first_name, profile.last_name]
    .filter((part): part is string => Boolean(part))
    .join(" ")
    .trim();
  return fullName || profile.username;
}

export function getProfileInitials(
  profile: Pick<Profile, "username" | "first_name" | "last_name">,
): string {
  const fullNameParts = [profile.first_name, profile.last_name].filter(
    (part): part is string => Boolean(part),
  );
  if (fullNameParts.length > 0) {
    return fullNameParts
      .slice(0, 2)
      .map((part) => part.charAt(0).toUpperCase())
      .join("");
  }

  return profile.username.charAt(0).toUpperCase();
}
