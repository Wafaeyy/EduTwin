"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import {
  getTwin,
  type StudentTwin,
} from "@/lib/api/twin";

function percentage(value: number) {
  return Math.round(value * 100);
}

function formatDate(date: string | null) {
  if (!date) {
    return "No deadline";
  }

  return new Date(date).toLocaleDateString(
    undefined,
    {
      year: "numeric",
      month: "short",
      day: "numeric",
    }
  );
}

function formatUpdatedDate(date: string) {
  return new Date(date).toLocaleString(
    undefined,
    {
      dateStyle: "medium",
      timeStyle: "short",
    }
  );
}

export default function MyTwinPage() {
  const [twin, setTwin] =
    useState<StudentTwin | null>(null);

  const [isLoading, setIsLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadTwin() {
      try {
        setError(null);

        const data = await getTwin();

        setTwin(data);
      } catch (error) {
        console.error(
          "Failed to load Digital Twin:",
          error
        );

        setError(
          "Unable to load your Digital Twin. Please try again."
        );
      } finally {
        setIsLoading(false);
      }
    }

    loadTwin();
  }, []);

  if (isLoading) {
    return (
      <main className="min-h-screen bg-zinc-50">
        <div className="mx-auto max-w-6xl px-8 py-10">
          <Link
            href="/"
            className="text-sm text-zinc-500 transition hover:text-zinc-900"
          >
            ← Back to EduTwin
          </Link>

          <div className="mt-16 flex justify-center">
            <p className="text-sm text-zinc-500">
              Loading your Digital Twin...
            </p>
          </div>
        </div>
      </main>
    );
  }

  if (!twin) {
    return (
      <main className="min-h-screen bg-zinc-50">
        <div className="mx-auto max-w-6xl px-8 py-10">
          <Link
            href="/"
            className="text-sm text-zinc-500 transition hover:text-zinc-900"
          >
            ← Back to EduTwin
          </Link>

          <div className="mt-10 rounded-2xl border border-red-200 bg-red-50 px-6 py-5">
            <p className="text-sm text-red-600">
              {error ?? "Unable to load your Digital Twin."}
            </p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen overflow-y-auto bg-zinc-50">
      <div className="mx-auto max-w-6xl px-8 py-10">

        {/* Header */}
        <div className="mb-8">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-zinc-500 transition hover:text-zinc-900"
          >
            ← Back to EduTwin
          </Link>

          <div className="mt-6">
            <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">
              My Digital Twin
            </h1>

            <p className="mt-2 text-sm text-zinc-500">
              Your evolving learning profile and current
              educational state.
            </p>
          </div>
        </div>

        {/* Identity Card */}
        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-5">

            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-zinc-900 text-xl font-semibold text-white">
              {twin.profile.full_name
                .charAt(0)
                .toUpperCase()}
            </div>

            <div className="min-w-0 flex-1">
              <h2 className="text-xl font-semibold text-zinc-900">
                {twin.profile.full_name}
              </h2>

              <p className="mt-1 text-sm text-zinc-500">
                {twin.profile.fied_of_study}
                {" · "}
                {twin.profile.education_stage}
              </p>

              <p className="mt-1 text-sm text-zinc-500">
                {twin.profile.university}
              </p>
            </div>

            <div className="hidden text-right sm:block">
              <p className="text-xs uppercase tracking-wide text-zinc-400">
                Last updated
              </p>

              <p className="mt-1 text-sm text-zinc-600">
                {formatUpdatedDate(
                  twin.last_updated
                )}
              </p>
            </div>
          </div>
        </section>

        {/* Overview */}
        <section className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">

          <div className="rounded-2xl border border-zinc-200 bg-white p-5">
            <p className="text-sm text-zinc-500">
              Goals
            </p>

            <p className="mt-2 text-3xl font-semibold text-zinc-900">
              {twin.goals.length}
            </p>

            <p className="mt-1 text-xs text-zinc-400">
              Learning objectives
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-200 bg-white p-5">
            <p className="text-sm text-zinc-500">
              Skills
            </p>

            <p className="mt-2 text-3xl font-semibold text-zinc-900">
              {twin.skills.length}
            </p>

            <p className="mt-1 text-xs text-zinc-400">
              Practical abilities
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-200 bg-white p-5">
            <p className="text-sm text-zinc-500">
              Interests
            </p>

            <p className="mt-2 text-3xl font-semibold text-zinc-900">
              {twin.interests.length}
            </p>

            <p className="mt-1 text-xs text-zinc-400">
              Areas of curiosity
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-200 bg-white p-5">
            <p className="text-sm text-zinc-500">
              Knowledge
            </p>

            <p className="mt-2 text-3xl font-semibold text-zinc-900">
              {twin.knowledge.length}
            </p>

            <p className="mt-1 text-xs text-zinc-400">
              Tracked concepts
            </p>
          </div>

        </section>

        {/* Goals */}
        <section className="mt-8 rounded-2xl border border-zinc-200 bg-white">
          <div className="border-b border-zinc-200 px-6 py-5">
            <h2 className="font-semibold text-zinc-900">
              Goals
            </h2>

            <p className="mt-1 text-sm text-zinc-500">
              What you are currently working toward.
            </p>
          </div>

          <div className="p-6">
            {twin.goals.length === 0 ? (
              <EmptyState text="No learning goals have been identified yet." />
            ) : (
              <div className="space-y-5">
                {twin.goals.map((goal) => (
                  <div
                    key={goal.goal_id}
                    className="rounded-xl border border-zinc-100 bg-zinc-50 p-5"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-medium text-zinc-900">
                          {goal.title}
                        </h3>

                        <p className="mt-1 text-sm text-zinc-500">
                          {goal.description}
                        </p>
                      </div>

                      <div className="flex gap-2">
                        <span className="rounded-full bg-white px-3 py-1 text-xs text-zinc-600 ring-1 ring-zinc-200">
                          {goal.priority}
                        </span>

                        <span className="rounded-full bg-white px-3 py-1 text-xs text-zinc-600 ring-1 ring-zinc-200">
                          {goal.status}
                        </span>
                      </div>
                    </div>

                    <div className="mt-5">
                      <div className="mb-2 flex justify-between text-xs">
                        <span className="text-zinc-500">
                          Progress
                        </span>

                        <span className="font-medium text-zinc-700">
                          {goal.progress}%
                        </span>
                      </div>

                      <div className="h-2 overflow-hidden rounded-full bg-zinc-200">
                        <div
                          className="h-full rounded-full bg-zinc-900 transition-all"
                          style={{
                            width: `${goal.progress}%`,
                          }}
                        />
                      </div>
                    </div>

                    <p className="mt-3 text-xs text-zinc-400">
                      Target:{" "}
                      {formatDate(
                        goal.target_completion_date
                      )}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Skills + Interests */}
        <div className="mt-8 grid gap-8 lg:grid-cols-2">

          {/* Skills */}
          <section className="rounded-2xl border border-zinc-200 bg-white">
            <div className="border-b border-zinc-200 px-6 py-5">
              <h2 className="font-semibold text-zinc-900">
                Skills
              </h2>

              <p className="mt-1 text-sm text-zinc-500">
                Practical abilities modeled by EduTwin.
              </p>
            </div>

            <div className="p-6">
              {twin.skills.length === 0 ? (
                <EmptyState text="No skills have been identified yet." />
              ) : (
                <div className="space-y-5">
                  {twin.skills.map((skill) => (
                    <div key={skill.skill_id}>
                      <div className="flex justify-between">
                        <div>
                          <p className="text-sm font-medium text-zinc-800">
                            {skill.name}
                          </p>

                          {skill.description && (
                            <p className="mt-1 text-xs text-zinc-400">
                              {skill.description}
                            </p>
                          )}
                        </div>

                        <span className="text-sm font-medium text-zinc-700">
                          {percentage(
                            skill.skill_level
                          )}
                          %
                        </span>
                      </div>

                      <div className="mt-2 h-2 overflow-hidden rounded-full bg-zinc-200">
                        <div
                          className="h-full rounded-full bg-zinc-900"
                          style={{
                            width: `${percentage(
                              skill.skill_level
                            )}%`,
                          }}
                        />
                      </div>

                      <p className="mt-2 text-xs text-zinc-400">
                        Twin confidence:{" "}
                        {percentage(
                          skill.confidence
                        )}
                        %
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* Interests */}
          <section className="rounded-2xl border border-zinc-200 bg-white">
            <div className="border-b border-zinc-200 px-6 py-5">
              <h2 className="font-semibold text-zinc-900">
                Interests
              </h2>

              <p className="mt-1 text-sm text-zinc-500">
                Topics that currently attract your attention.
              </p>
            </div>

            <div className="p-6">
              {twin.interests.length === 0 ? (
                <EmptyState text="No interests have been identified yet." />
              ) : (
                <div className="space-y-5">
                  {twin.interests.map(
                    (interest) => (
                      <div
                        key={
                          interest.interest_id
                        }
                      >
                        <div className="flex justify-between">
                          <div>
                            <p className="text-sm font-medium text-zinc-800">
                              {interest.topic}
                            </p>

                            {interest.description && (
                              <p className="mt-1 text-xs text-zinc-400">
                                {
                                  interest.description
                                }
                              </p>
                            )}
                          </div>

                          <span className="text-sm font-medium text-zinc-700">
                            {percentage(
                              interest.affinity
                            )}
                            %
                          </span>
                        </div>

                        <div className="mt-2 h-2 overflow-hidden rounded-full bg-zinc-200">
                          <div
                            className="h-full rounded-full bg-zinc-900"
                            style={{
                              width: `${percentage(
                                interest.affinity
                              )}%`,
                            }}
                          />
                        </div>

                        <p className="mt-2 text-xs text-zinc-400">
                          Twin confidence:{" "}
                          {percentage(
                            interest.confidence
                          )}
                          %
                        </p>
                      </div>
                    )
                  )}
                </div>
              )}
            </div>
          </section>
        </div>

        {/* Knowledge */}
        <section className="mt-8 rounded-2xl border border-zinc-200 bg-white">
          <div className="border-b border-zinc-200 px-6 py-5">
            <h2 className="font-semibold text-zinc-900">
              Knowledge & Mastery
            </h2>

            <p className="mt-1 text-sm text-zinc-500">
              Current estimates of your understanding
              across educational concepts.
            </p>
          </div>

          <div className="p-6">
            {twin.knowledge.length === 0 ? (
              <EmptyState text="No knowledge has been modeled yet." />
            ) : (
              <div className="grid gap-5 md:grid-cols-2">
                {twin.knowledge.map(
                  (knowledge) => (
                    <div
                      key={
                        knowledge.knowledge_id
                      }
                      className="rounded-xl border border-zinc-100 bg-zinc-50 p-5"
                    >
                      <div className="flex justify-between gap-4">
                        <div>
                          <h3 className="text-sm font-medium text-zinc-800">
                            {knowledge.title}
                          </h3>

                          {knowledge.description && (
                            <p className="mt-1 text-xs text-zinc-400">
                              {
                                knowledge.description
                              }
                            </p>
                          )}
                        </div>

                        <span className="text-sm font-semibold text-zinc-700">
                          {percentage(
                            knowledge.mastery
                          )}
                          %
                        </span>
                      </div>

                      <div className="mt-4 h-2 overflow-hidden rounded-full bg-zinc-200">
                        <div
                          className="h-full rounded-full bg-zinc-900"
                          style={{
                            width: `${percentage(
                              knowledge.mastery
                            )}%`,
                          }}
                        />
                      </div>

                      <p className="mt-2 text-xs text-zinc-400">
                        Twin confidence:{" "}
                        {percentage(
                          knowledge.confidence
                        )}
                        %
                      </p>
                    </div>
                  )
                )}
              </div>
            )}
          </div>
        </section>

        {/* Preferences */}
        <section className="mt-8 rounded-2xl border border-zinc-200 bg-white">
          <div className="border-b border-zinc-200 px-6 py-5">
            <h2 className="font-semibold text-zinc-900">
              Learning Preferences
            </h2>

            <p className="mt-1 text-sm text-zinc-500">
              Contextual preferences inferred by EduTwin.
            </p>
          </div>

          <div className="p-6">
            {twin.preferences.length === 0 ? (
              <EmptyState text="No learning preferences have been modeled yet." />
            ) : (
              <div className="grid gap-5 md:grid-cols-2">
                {twin.preferences.map(
                  (preference) => (
                    <div
                      key={
                        preference.preference_id
                      }
                      className="rounded-xl border border-zinc-100 bg-zinc-50 p-5"
                    >
                      <div>
                        <h3 className="text-sm font-medium text-zinc-800">
                          {preference.dimension}
                        </h3>

                        <p className="mt-1 text-xs text-zinc-400">
                          {preference.context}
                        </p>
                      </div>

                      <div className="mt-4 space-y-3">
                        {Object.entries(
                          preference.affinities
                        ).map(
                          ([option, value]) => (
                            <div key={option}>
                              <div className="flex justify-between text-xs">
                                <span className="text-zinc-500">
                                  {option}
                                </span>

                                <span className="font-medium text-zinc-700">
                                  {percentage(
                                    value
                                  )}
                                  %
                                </span>
                              </div>

                              <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-zinc-200">
                                <div
                                  className="h-full rounded-full bg-zinc-900"
                                  style={{
                                    width: `${percentage(
                                      value
                                    )}%`,
                                  }}
                                />
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )
                )}
              </div>
            )}
          </div>
        </section>

        {/* Footer */}
        <div className="py-8 text-center text-xs text-zinc-400">
          Your Digital Twin evolves as EduTwin learns
          from your interactions.
        </div>
      </div>
    </main>
  );
}

function EmptyState({
  text,
}: {
  text: string;
}) {
  return (
    <div className="rounded-xl border border-dashed border-zinc-200 px-6 py-10 text-center">
      <p className="text-sm text-zinc-400">
        {text}
      </p>
    </div>
  );
}