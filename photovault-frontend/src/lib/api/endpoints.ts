export const endpoints = {
  // auth
  csrf: "/api/auth/csrf/",
  login: "/api/auth/login/",
  signup: "/api/auth/register/",
  logout: "/api/auth/logout/",
  verify: "/api/auth/verify/",
  refresh: "/api/auth/refresh/",
  me: "/api/auth/me/",
  passwordResetRequest: "/api/auth/password/reset/",
  passwordReset: "/api/auth/password/reset/confirm/",
  emailVerify: "/api/auth/verify/",
  emailResend: "/api/auth/verify/resend/",
  accountDelete: "/api/auth/delete/",
  googleOAuth: "/api/auth/google/",

  // dashboard
  dashStats: "/api/dashboard/stats",
  dashRecent: "/api/dashboard/recent-activity",
  dashStorage: "/api/dashboard/storage-analysis",
  dashPerson: "/api/dashboard/person-analysis",
  dashLocation: "/api/dashboard/location-analysis",
  dashSuggestions: "/api/dashboard/search-suggestions",

  // images
  images: "/api/images/",
  imageThumb: (id: string) => `/api/images/${id}/thumb`,
  imageView: (id: string) => `/api/images/${id}/view`,
  imageDelete: (id: string) => `/api/images/${id}`,

  imageUpload: "/api/images/upload",
  imageBulkUpload: "/api/images/bulk/upload",
  imageBulkDelete: "/api/images/bulk/delete",

  // albums
  albums: "/api/albums/",
  album: (id: string) => `/api/albums/${id}`,
  albumImages: (id: string) => `/api/albums/${id}/images`,
  albumCreateManual: "/api/albums/manual",
  albumAutoGenerate: "/api/albums/auto-generate",
  albumAutoCategorize: "/api/albums/auto-categorize",
  albumAddImages: (id: string) => `/api/albums/${id}/add-images`,
  albumRemoveImages: (id: string) => `/api/albums/${id}/remove-images`,
  albumDelete: (id: string) => `/api/albums/${id}`,
  albumQR: (id: string) => `/api/albums/${id}/qr`,

  // search
  search: "/api/images/search/",
  searchSuggestions: "/api/images/search/suggestions",

  // persons
  personClusters: "/api/persons/clusters",
  personRename: (id: string) => `/api/persons/clusters/${id}/rename`,

  // sharing
  shareCreate: "/api/link/create",
  shareVerify: "/api/link/verify",
  shareList: (albumId: string) => `/api/link/list/${albumId}`,
  shareRevoke: (shareId: string) => `/api/link/revoke/${shareId}`,

  // facial
  faceRegister: "/api/facial/register",
  faceVerify: "/api/facial/verify",

  // metadata
  metadataImage: (id: string) => `/api/metadata/images/${id}`,
  metadataEvents: "/api/metadata/events",

  // public share
  publicShare: (token: string) => `/shared/${token}`,
  publicShareImage: (token: string, imageId: string) => `/shared/${token}/image/${imageId}`,

  // face claim
  faceClaimInit: (token: string) => `/public/face-claim/${token}`,
  faceClaimScan: (token: string) => `/public/face-claim/${token}/scan`,
  faceClaimVerify: (token: string) => `/public/face-claim/${token}/verify`,
  faceClaimGallery: (token: string) => `/public/face-claim/${token}/gallery`,
  faceClaimImage: (token: string, imageId: string) => `/public/face-claim/${token}/image/${imageId}`,
  faceClaimThumb: (token: string, imageId: string) => `/public/face-claim/${token}/image/${imageId}/thumb`,

  // admin
  adminPersonAlbums: "/admin/person-albums",
  adminShareCreateForPersonAlbum: (albumId: string) => `/admin/person-albums/${albumId}/share`,
  adminShareQrForPersonAlbum: (albumId: string) => `/admin/person-albums/${albumId}/share/qr`,
  adminRevokeShare: (shareId: string) => `/admin/shares/${shareId}/revoke`,
  adminShareStats: (shareId: string) => `/admin/shares/${shareId}/stats`,
};
