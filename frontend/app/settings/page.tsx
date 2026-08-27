"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import {
  getProfile,
  updateProfile,
  type Profile,
} from "@/lib/api/profile";

export default function SettingsPage() {
  const [profile, setProfile] = useState<Profile | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  /*
   * Load the current profile from the backend.
   */
  useEffect(() => {
    async function loadProfile() {
      try {
        setError(null);

        const data = await getProfile();

        setProfile(data);
      } catch (error) {
        console.error("Failed to load profile:", error);

        setError(
          "Unable to load your profile. Please try again."
        );
      } finally {
        setIsLoading(false);
      }
    }

    loadProfile();
  }, []);

  /*
   * Update one profile field.
   */
  function handleChange(
    field: keyof Profile,
    value: string | number | null
  ) {
    if (!profile) {
      return;
    }

    setProfile({
      ...profile,
      [field]: value,
    });

    setSuccess(false);
  }

  /*
   * Save the edited profile to the backend.
   */
  async function handleSave() {
    if (!profile || isSaving) {
      return;
    }

    try {
      setError(null);
      setSuccess(false);
      setIsSaving(true);

      const updatedProfile = await updateProfile(
        profile
      );

      setProfile(updatedProfile);
      setSuccess(true);
    } catch (error) {
      console.error(
        "Failed to update profile:",
        error
      );

      setError(
        "Unable to save your changes. Please try again."
      );
    } finally {
      setIsSaving(false);
    }
  }

  /*
   * Loading state.
   */
  if (isLoading) {
    return (
      <main className="min-h-screen bg-zinc-50">
        <div className="mx-auto max-w-4xl px-8 py-10">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-zinc-500 transition hover:text-zinc-900"
          >
            <span>←</span>
            <span>Back to EduTwin</span>
          </Link>

          <div className="mt-12 flex items-center justify-center">
            <p className="text-sm text-zinc-500">
              Loading your profile...
            </p>
          </div>
        </div>
      </main>
    );
  }

  /*
   * Error state when the profile could not be loaded.
   */
  if (!profile) {
    return (
      <main className="min-h-screen bg-zinc-50">
        <div className="mx-auto max-w-4xl px-8 py-10">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-zinc-500 transition hover:text-zinc-900"
          >
            <span>←</span>
            <span>Back to EduTwin</span>
          </Link>

          <div className="mt-10 rounded-2xl border border-red-200 bg-red-50 px-6 py-5">
            <p className="text-sm text-red-600">
              {error ?? "Unable to load your profile."}
            </p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen overflow-y-auto bg-zinc-50">
      <div className="mx-auto max-w-4xl px-8 py-10">
        {/* Header */}
        <div className="mb-10">
          <Link
            href="/"
            className="mb-6 inline-flex items-center gap-2 text-sm text-zinc-500 transition hover:text-zinc-900"
          >
            <span>←</span>
            <span>Back to EduTwin</span>
          </Link>

          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">
            Settings
          </h1>

          <p className="mt-2 text-sm text-zinc-500">
            Manage your account and EduTwin experience.
          </p>
        </div>

        <div className="space-y-8">
          {/* Account */}
          <section className="rounded-2xl border border-zinc-200 bg-white">
            <div className="border-b border-zinc-200 px-6 py-5">
              <h2 className="text-base font-semibold text-zinc-900">
                Account
              </h2>

              <p className="mt-1 text-sm text-zinc-500">
                Manage your personal account information.
              </p>
            </div>

            <div className="space-y-6 p-6">
              {/* Name */}
              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-700">
                  Name
                </label>

                <input
                  type="text"
                  value={profile.full_name}
                  onChange={(event) =>
                    handleChange(
                      "full_name",
                      event.target.value
                    )
                  }
                  className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-zinc-400 focus:ring-2 focus:ring-zinc-100"
                />
              </div>

              {/* Email */}
              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-700">
                  Email
                </label>

                <input
                  type="email"
                  value={profile.email}
                  onChange={(event) =>
                    handleChange(
                      "email",
                      event.target.value
                    )
                  }
                  className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-zinc-400 focus:ring-2 focus:ring-zinc-100"
                />
              </div>

              {/* Education Stage */}
<div>
  <label className="mb-2 block text-sm font-medium text-zinc-700">
    Education stage
  </label>

  <select
    value={profile.education_stage}
    onChange={(event) =>
      handleChange(
        "education_stage",
        event.target.value
      )
    }
    className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-900 outline-none transition focus:border-zinc-400 focus:ring-2 focus:ring-zinc-100"
  >
    <option value="High School">
      High School
    </option>

    <option value="Undergraduate Year 1">
      Undergraduate Year 1
    </option>

    <option value="Undergraduate Year 2">
      Undergraduate Year 2
    </option>

    <option value="Undergraduate Year 3">
      Undergraduate Year 3
    </option>

    <option value="Undergraduate Year 4">
      Undergraduate Year 4
    </option>

    <option value="Undergraduate Year 5">
      Undergraduate Year 5
    </option>

    <option value="Master's">
      Master's
    </option>

    <option value="PhD">
      PhD
    </option>

    <option value="Professional">
      Professional
    </option>

    <option value="Self Learner">
      Self Learner
    </option>
  </select>
</div>

              {/* University */}
              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-700">
                  University
                </label>

                <input
                  type="text"
                  value={profile.university}
                  onChange={(event) =>
                    handleChange(
                      "university",
                      event.target.value
                    )
                  }
                  className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-zinc-400 focus:ring-2 focus:ring-zinc-100"
                />
              </div>

              {/* Save */}
              <div className="flex items-center justify-between border-t border-zinc-100 pt-5">
                <div>
                  {success && (
                    <p className="text-sm text-green-600">
                      Changes saved successfully.
                    </p>
                  )}

                  {error && (
                    <p className="text-sm text-red-600">
                      {error}
                    </p>
                  )}
                </div>

                <button
                  type="button"
                  onClick={handleSave}
                  disabled={isSaving}
                  className="rounded-xl bg-zinc-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isSaving
                    ? "Saving..."
                    : "Save changes"}
                </button>
              </div>
            </div>
          </section>

          {/* Appearance */}
          <section className="rounded-2xl border border-zinc-200 bg-white">
            <div className="border-b border-zinc-200 px-6 py-5">
              <h2 className="text-base font-semibold text-zinc-900">
                Appearance
              </h2>

              <p className="mt-1 text-sm text-zinc-500">
                Customize how EduTwin looks and behaves.
              </p>
            </div>

            <div className="divide-y divide-zinc-100">
              {/* Theme */}
              <div className="flex items-center justify-between gap-6 px-6 py-5">
                <div>
                  <p className="text-sm font-medium text-zinc-800">
                    Theme
                  </p>

                  <p className="mt-1 text-sm text-zinc-500">
                    Choose the appearance of EduTwin.
                  </p>
                </div>

                <select
                  defaultValue="system"
                  className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-700 outline-none focus:border-zinc-400"
                >
                  <option value="system">
                    System
                  </option>

                  <option value="light">
                    Light
                  </option>

                  <option value="dark">
                    Dark
                  </option>
                </select>
              </div>

              {/* Interface Preferences */}
              <div className="flex items-center justify-between gap-6 px-6 py-5">
                <div>
                  <p className="text-sm font-medium text-zinc-800">
                    Interface preferences
                  </p>

                  <p className="mt-1 text-sm text-zinc-500">
                    Customize the way EduTwin's
                    interface behaves.
                  </p>
                </div>

                <button
                  type="button"
                  className="rounded-lg border border-zinc-200 px-3 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50"
                >
                  Configure
                </button>
              </div>
            </div>
          </section>

          {/* Data & Privacy */}
          <section className="rounded-2xl border border-zinc-200 bg-white">
            <div className="border-b border-zinc-200 px-6 py-5">
              <h2 className="text-base font-semibold text-zinc-900">
                Data & Privacy
              </h2>

              <p className="mt-1 text-sm text-zinc-500">
                Manage your EduTwin data and privacy.
              </p>
            </div>

            <div className="divide-y divide-zinc-100">
              {/* Export */}
              <div className="flex items-center justify-between gap-6 px-6 py-5">
                <div>
                  <p className="text-sm font-medium text-zinc-800">
                    Export data
                  </p>

                  <p className="mt-1 text-sm text-zinc-500">
                    Download a copy of your EduTwin
                    data.
                  </p>
                </div>

                <button
                  type="button"
                  className="rounded-lg border border-zinc-200 px-3 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50"
                >
                  Export
                </button>
              </div>

              {/* Delete */}
              <div className="flex items-center justify-between gap-6 px-6 py-5">
                <div>
                  <p className="text-sm font-medium text-zinc-800">
                    Delete data
                  </p>

                  <p className="mt-1 text-sm text-zinc-500">
                    Permanently delete your EduTwin
                    data.
                  </p>
                </div>

                <button
                  type="button"
                  className="rounded-lg border border-red-200 px-3 py-2 text-sm font-medium text-red-600 transition hover:bg-red-50"
                >
                  Delete data
                </button>
              </div>
            </div>
          </section>
        </div>

        <p className="mt-8 text-center text-xs text-zinc-400">
          EduTwin
        </p>
      </div>
    </main>
  );
}