// import { Button } from "@/components/ui/button";
// import { Spinner } from "@/components/ui/spinner"
// import { useState } from "react";
//
// export default function MainRecognitionPage() {
//    const [modelLoaded, setModelLoaded] = useState<boolean>(false);
//    const [modelLoading, setModelLoading] = useState<boolean>(false);
//    const [latestPartialText, setLatestPartialText] = useState<string>("");
//    const [latestText, setLatestText] = useState<string>("");
//
//    const loadModel = async () => {
//       setModelLoading(true);
//       const response = await fetch("https://127.0.0.1:5000/api/load_model");
//       const data = await response.json();
//
//       if (data.status === "success") {
//          setModelLoaded(true);
//          setModelLoading(false);
//          alert("Model loaded successfully");
//       } else {
//          console.error("[!] error loading model");
//          setModelLoading(false);
//       }
//    };
//
//    const getLatestPartialText = async () => {
//       if(!modelLoaded) {
//          return "Model has not laoded yet";
//       }
//       const response = await fetch("https://127.0.0.1:5000/api/get_latest_partial_text");
//       const data = await response.json();
//       setLatestPartialText(data);
//    };
//
//    const getLatestText = async () => {
//       if(!modelLoaded) {
//          return "Model has not loaded yet";
//       }
//       const response = await fetch("https://127.0.0.1:5000/api/get_latest_text");
//       const data = await response.json();
//       setLatestText(data);
//    };
//
//    return (
//       <div className="m-3 flex flex-col items-center justify-center min-h-screen gap-4 p-4">
//          <Button
//             disabled={modelLoaded || modelLoading}
//             onClick={loadModel}
//             variant="outline"
//          >
//             {modelLoaded ? (
//                <p>Model Loaded</p>
//             ) : modelLoading ? (
//                <p>
//                   <Spinner />
//                   Loading Model
//                </p>
//             ) : (
//                <p>Load Model</p>
//             )}
//          </Button>
//          <div className="flex felx-col gap-3 items-center w-full h-[500px]">
//             <p>{latestText}</p>
//             <p>{latestPartialText}</p>
//          </div>
//       </div>
//    );
// }

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { useEffect, useState } from "react";

export default function MainRecognitionPage() {
  const [modelLoaded, setModelLoaded] = useState(false);
  const [modelLoading, setModelLoading] = useState(false);
  const [latestPartialText, setLatestPartialText] = useState("");
  const [latestText, setLatestText] = useState("");

  const loadModel = async () => {
    setModelLoading(true);
    const response = await fetch("http://127.0.0.1:5000/api/load_model");
    const data = await response.json();

    console.log(data)

    if (data.status === "success") {
      setModelLoaded(true);
      alert("Model loaded successfully");
    } else {
      console.error("[!] error loading model");
    }

    setModelLoading(false);
  };

  const fetchLatestPartialText = async () => {
    if (!modelLoaded) return;

    const response = await fetch(
      "http://127.0.0.1:5000/api/get_latest_partial_text"
    );
    const data = await response.json();
    setLatestPartialText(data);
  };

  const fetchLatestText = async () => {
    if (!modelLoaded) return;

    const response = await fetch(
      "http://127.0.0.1:5000/api/get_latest_text"
    );
    const data = await response.json();
    setLatestText(data);
  };

  useEffect(() => {
    if (!modelLoaded) return;

    const interval = setInterval(() => {
      fetchLatestText();
      fetchLatestPartialText();
    }, 100);

    return () => clearInterval(interval);
  }, [modelLoaded]);

  return (
    <div className="m-3 flex flex-col items-center w-full justify-center min-h-screen gap-4 p-4">
      <Button
        disabled={modelLoaded || modelLoading}
        onClick={loadModel}
        variant="outline"
      >
        {modelLoaded ? (
          <p>Model Loaded</p>
        ) : modelLoading ? (
          <p className="flex gap-x-2 items-center justify-center">
            <Spinner /> Loading Model
          </p>
        ) : (
          <p>Load Model</p>
        )}
      </Button>

      <div className="flex flex-col gap-3 items-center justify-center w-full">
        <p className="text-7xl font-bold w-full break-words">{latestText}</p>
        <p className="w-full break-words">{latestPartialText}</p>
      </div>
    </div>
  );
}
