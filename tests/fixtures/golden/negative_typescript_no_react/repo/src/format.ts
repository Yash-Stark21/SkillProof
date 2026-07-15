export type Profile = {
  name: string;
};

export function formatProfile(profile: Profile): string {
  return profile.name.toUpperCase();
}
