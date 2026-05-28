EXPECTED_MIME_TYPES = {
    'md': 'text/markdown',
    'pdf': 'application/pdf'
}

BLOCKED_EXTENSIONS = frozenset({
    '.py', '.sh', '.bat', '.cmd', '.ps1', '.exe', '.js',
    '.msi', '.vbs', '.wsf', '.jar', '.scr', '.cpl',
    '.hta', '.wsh', '.scf', '.lnk', '.reg', '.inf',
    '.iso', '.dmg',
    '.docm', '.xlsm', '.pptm',
    '.dotm', '.xltm', '.ppsm',
    '.odt',                                              
    '.zip', '.tar', '.tar.gz', '.rar', '.7z',
    '.apk',
    '.dll', '.drv', '.vxd', '.sys',
    '.bak', '.old', '.swp',
    '.chm', '.mdb', '.sql', '.db'
})

VALID_FORMAT_IMAGES = [
    'png',
    'jpg',
    'jpeg',
    'bmp',
    'tiff',
    'svg',
    'webp',
    'heic',
    'heif'
]

EXPECTED_IMAGE_MIME_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "tiff": "image/tiff",
    "svg": "image/svg+xml"
}

OUTPUT_PATH = 'src/temp'