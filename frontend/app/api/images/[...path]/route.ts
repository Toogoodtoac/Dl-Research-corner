import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const resolvedParams = await params;
    const imagePath = resolvedParams.path.join('/');
    
    // Redirect image requests to the backend
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const redirectUrl = `${backendUrl}/data/${imagePath}`;
    
    return NextResponse.redirect(redirectUrl);
  } catch (error) {
    console.error('Error in image route:', error);
    return NextResponse.json(
      { error: 'Failed to process image request' },
      { status: 500 }
    );
  }
}
