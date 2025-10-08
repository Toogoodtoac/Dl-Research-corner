"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import { ArrowLeft, AlertCircle } from "lucide-react";
import { getImageById, SearchResult } from "@/services/api";
import { getLocalImageUrl } from "@/lib/utils";
import { toast } from "sonner";

export default function ImageDetail() {
  const params = useParams();
  const router = useRouter();
  const [image, setImage] = useState<SearchResult | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error] = useState<string | null>(null);
  const [imageError, setImageError] = useState(false);

  const imageId = params.id as string;

  useEffect(() => {
    if (imageId) {
      getImageById(imageId).then((image) => {
        setImage(image);
        setIsLoading(false);
      });
    }
  }, [imageId]);

  useEffect(() => {
    if (image?.image_url) {
      // Use the backend's image_url field and make it absolute
      const backendUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      setImageUrl(`${backendUrl}${image.image_url}`);
    } else {
      // Fallback to local image URL (for backward compatibility)
      const localImageUrl = getLocalImageUrl();
      console.log(localImageUrl);
      setImageUrl(localImageUrl);
    }
  }, [imageId, image?.image_url]);

  const handleBack = () => {
    // Navigate back to search page with preserved state
    // The main page will automatically restore the search state from localStorage
    router.push("/");
  };

  const handleImageError = () => {
    setImageError(true);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center mx-auto px-4 py-8 min-h-[50vh] container">
        <div className="border-gray-900 border-t-2 border-b-2 rounded-full w-12 h-12 animate-spin"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto px-4 py-8 container">
        <button
          onClick={handleBack}
          className="flex items-center mb-6 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="mr-2 w-4 h-4" />
          Back to search
        </button>
        <div className="p-8 border border-red-200 rounded-lg text-red-500 text-center">
          {error}
        </div>
      </div>
    );
  }
  if (!image) {
    return (
      <div className="mx-auto px-4 py-8 container">
        <button
          onClick={handleBack}
          className="flex items-center mb-6 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="mr-2 w-4 h-4" />
          Back to search
        </button>
        <div className="p-8 border border-red-200 rounded-lg text-red-500 text-center">
          Image not found
        </div>
      </div>
    );
  }
  const handleCopyId = () => {
    console.log(image);
    if (image?.image_id) {
      console.log(image?.image_id);
      navigator.clipboard.writeText(image?.image_id);
      toast.success(`Image ID ${image?.image_id} copied to clipboard`);
    } else {
      toast.error("Image ID not found");
    }
  };

  return (
    <div className="mx-auto px-4 py-8 container">
      <button
        onClick={handleBack}
        className="flex items-center mb-6 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="mr-2 w-4 h-4" />
        Back to search
      </button>

      {image && (
        <div className="bg-white shadow-lg rounded-lg overflow-hidden">
          <div className="relative w-full h-[60vh]">
            {imageError ? (
              <div className="absolute inset-0 flex flex-col justify-center items-center bg-gray-100">
                <AlertCircle className="mb-4 w-12 h-12 text-gray-400" />
                <p className="font-medium text-gray-600">Image not available</p>
                <p className="mt-2 text-gray-500 text-sm">
                  Unable to load image with ID: {image.image_id}
                </p>
              </div>
            ) : (
              <Image
                src={imageUrl || "/placeholder.svg"}
                alt={`Image ${image?.image_id}`}
                fill
                className="object-contain"
                priority
                onError={handleImageError}
              />
            )}
          </div>

          <div className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h1 className="font-bold text-2xl">
                Image ID: {image?.image_id}
              </h1>
              <button
                onClick={handleCopyId}
                className="bg-gray-100 hover:bg-gray-200 px-4 py-2 rounded-md text-sm"
              >
                Copy ID
              </button>
            </div>

            <div className="gap-4 grid grid-cols-1 md:grid-cols-2">
              <div>
                <h2 className="mb-2 font-semibold text-lg">Details</h2>
                <p className="mb-1 text-gray-700">
                  Video ID: {image?.image_id.split("_").slice(0, 2).join("_")}
                </p>
                <p className="mb-1 text-gray-700">
                  Timestamp: {image?.frame_stamp}
                </p>
              </div>

              <div>
                <h2 className="mb-2 font-semibold text-lg">Actions</h2>
                <a
                  href={`${image?.watch_url}&t=${Math.floor(image?.frame_stamp || 0)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-md text-white"
                >
                  Open Video
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
