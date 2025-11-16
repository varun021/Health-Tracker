"use client";
import { useState } from "react";
import { userApi } from "@/lib/api-services"; // ...use centralized api service...

export default function TrainModelButton() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const trainModel = async () => {
    if (!confirm("Are you sure you want to train the ML model?")) return;

    setLoading(true);
    try {
      const data = await userApi.trainModel();
      setResult(data);
      alert("Model trained successfully!");
    } catch (error) {
      console.error(error);
      alert(error?.response?.data?.error || "Training failed!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full mt-6 bg-gray-900 p-4 rounded-lg">
      <button
        onClick={trainModel}
        disabled={loading}
        className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg"
      >
        {loading ? "Training Model..." : "Train ML Model"}
      </button>

      {result && (
        <pre className="mt-4 text-green-400">
{JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
