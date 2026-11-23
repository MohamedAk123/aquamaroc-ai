import { Workspace } from "../../../components/workspace";
export default async function Barrage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <Workspace view="detail" reservoirId={id} />;
}
