export function pickToken(data: any): string | null {
  // Try multiple possible token field names
  return (
    data?.access_token ??
    data?.token ??
    data?.jwt ??
    data?.data?.access_token ??
    data?.data?.token ??
    null
  );
}

export function formatBytesMB(mb: number) {
  return `${Math.round(mb)} MB`;
}

export function formatDate(date: Date | string) {
  return new Date(date).toLocaleDateString();
}

