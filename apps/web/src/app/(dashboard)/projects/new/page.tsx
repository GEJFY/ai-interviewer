'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/**
 * /projects/new へのアクセスを /projects にリダイレクト
 * 案件作成は案件一覧ページのモーダルで行う
 */
export default function NewProjectRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/projects');
  }, [router]);

  return null;
}
