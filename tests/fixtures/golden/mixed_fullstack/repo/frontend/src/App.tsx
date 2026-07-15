import { useEffect, useState } from "react";

export function App(): JSX.Element {
  const [name, setName] = useState("loading");

  useEffect(() => {
    setName("Ada");
  }, []);

  return <main>{name}</main>;
}
