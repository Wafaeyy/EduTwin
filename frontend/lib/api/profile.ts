export type Profile = {
  full_name: string;
  email: string;
  university: string;
  fied_of_study: string;
  education_stage: string;
  current_year: number | null;
};

const API_BASE_URL = "http://127.0.0.1:8000";

export async function getProfile(): Promise<Profile> {
  const response = await fetch(
    `${API_BASE_URL}/twin/profile`
  );

  if (!response.ok) {
    throw new Error("Failed to load profile.");
  }

  return response.json();
}

export async function updateProfile(
  profile: Profile
): Promise<Profile> {
  const response = await fetch(
    `${API_BASE_URL}/twin/profile`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(profile),
    }
  );

  if (!response.ok) {
    throw new Error("Failed to update profile.");
  }

  return response.json();
}