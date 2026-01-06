import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useState, useEffect } from "react"
import MainRecognitionPage from "./MainRecognitionPage"

async function fetchDevices() {
   try {
      const response = await fetch("http://127.0.0.1:5000/api/list_devices");
      if(!response.ok) {
         throw new Error(`HTTP ERROR: ${response.status}`);
      }
      const data = await response.json();
      return data;
   } catch (error) {
      console.error("Error retreiving devices: ", error);
      return [];
   }
}

export default function App() {
   const [devices, setDevices] = useState<{index: number, name: string}[]>([]);
   const [deviceIndex, setDeviceIndex] = useState<string>("");
   const [ok, setOk] = useState<boolean>(false);

   const refreshList = async () => {
      const data = await fetchDevices();
      setDevices(data);
   };

   const submitDeviceIndex = async () => {
      if(deviceIndex === "" || isNaN(Number(deviceIndex))) {
         alert("Please enter a valid index");
         return;
      }

      const response = await fetch("http://127.0.0.1:5000/api/use_device", {
         method: "POST",
         headers: {
            "Content-Type": "application/json",
         },
         body: JSON.stringify({
            device_id: Number(deviceIndex)
         }),
      });

      const data = await response.json();
      if(data.status == "success") {
         setOk(true);
      }

      console.log("Device selected", deviceIndex);
      console.log("Response: ", data);
   }

   useEffect(() => {
      refreshList();
   }, []);

   if (ok) return <MainRecognitionPage />;

   return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4 p-4">
         <div className="flex flex-col w-200 gap-5">
            <Button variant="outline" onClick={refreshList}>Refresh device List</Button>
            <ScrollArea className="h-[200px] w-200 rounded-md border p-4">
              <ul>
                {devices.map((device) => (
                  <li key={device.index}>
                    index: {device.index} device: {device.name}
                  </li>
                ))}
              </ul>
            </ScrollArea>
            <Input 
               placeholder="Enter the index of the device you want to use" 
               value={deviceIndex}
               onChange={(e) => setDeviceIndex(e.target.value)}
            />
            <Button onClick={submitDeviceIndex}>Submit</Button>
         </div>
      </div>
   );
}
