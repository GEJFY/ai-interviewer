'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  BookOpen,
  MessageSquare,
  Calendar,
  Tag,
  ChevronRight,
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface KnowledgeItem {
  id: string;
  title: string;
  content: string;
  source_type: string;
  source_interview_id: string | null;
  tags: string[];
  created_at: string;
  relevance_score?: number;
}

export default function KnowledgePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const { data: searchResults, refetch } = useQuery({
    queryKey: ['knowledge-search', searchQuery],
    queryFn: async () => {
      if (!searchQuery.trim()) return null;
      const response = await apiClient.post('/knowledge/search', {
        query: searchQuery,
        limit: 20,
      });
      return response.data;
    },
    enabled: false,
  });

  const { data: recentItems, isLoading: isLoadingRecent } = useQuery({
    queryKey: ['knowledge-recent'],
    queryFn: async () => {
      const response = await apiClient.get('/knowledge', {
        params: { page: 1, pageSize: 10 },
      });
      return response.data;
    },
  });

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    await refetch();
    setIsSearching(false);
  };

  const getSourceLabel = (type: string) => {
    switch (type) {
      case 'interview': return 'インタビュー';
      case 'document': return 'ドキュメント';
      case 'manual': return '手動入力';
      default: return type;
    }
  };

  const renderKnowledgeItem = (item: KnowledgeItem, showRelevance = false) => (
    <div key={item.id} className="px-6 py-4 hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors">
      <div className="flex items-start gap-4">
        <div className="p-2 bg-accent-500/10 rounded-lg">
          <BookOpen className="w-5 h-5 text-accent-500" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-medium text-surface-900 dark:text-surface-100">{item.title}</h3>
            {showRelevance && item.relevance_score && (
              <Badge variant="success">
                関連度 {Math.round(item.relevance_score * 100)}%
              </Badge>
            )}
          </div>
          <p className="text-sm text-surface-500 dark:text-surface-400 line-clamp-2 mb-2">
            {item.content}
          </p>
          <div className="flex items-center gap-4 text-xs text-surface-400">
            <span className="flex items-center gap-1">
              <MessageSquare className="w-3 h-3" />
              {getSourceLabel(item.source_type)}
            </span>
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {format(new Date(item.created_at), 'yyyy/MM/dd', { locale: ja })}
            </span>
            {item.tags.length > 0 && (
              <span className="flex items-center gap-1">
                <Tag className="w-3 h-3" />
                {item.tags.slice(0, 3).join(', ')}
              </span>
            )}
          </div>
        </div>
        <ChevronRight className="w-5 h-5 text-surface-300 dark:text-surface-600" />
      </div>
    </div>
  );

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-50">ナレッジ検索</h1>
        <p className="text-surface-500 dark:text-surface-400 mt-1">
          過去のインタビューから蓄積されたナレッジを検索できます
        </p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="キーワードや質問を入力して検索..."
            className="w-full pl-12 pr-4 py-3 bg-white dark:bg-surface-800 border border-surface-300 dark:border-surface-600 rounded-xl text-surface-900 dark:text-surface-100 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500 transition-all"
          />
        </div>
        <Button variant="accent" type="submit" isLoading={isSearching}>
          検索
        </Button>
      </form>

      {searchResults?.items && searchResults.items.length > 0 && (
        <Card>
          <div className="px-6 py-4 border-b border-surface-200 dark:border-surface-700">
            <h2 className="font-semibold text-surface-900 dark:text-surface-50">
              検索結果 ({searchResults.items.length}件)
            </h2>
          </div>
          <div className="divide-y divide-surface-100 dark:divide-surface-800">
            {searchResults.items.map((item: KnowledgeItem) => renderKnowledgeItem(item, true))}
          </div>
        </Card>
      )}

      {searchResults?.items && searchResults.items.length === 0 && (
        <Card className="p-12 text-center">
          <Search className="w-12 h-12 text-surface-300 dark:text-surface-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-surface-900 dark:text-surface-50 mb-2">
            検索結果がありません
          </h3>
          <p className="text-surface-500 dark:text-surface-400">
            別のキーワードで検索してください
          </p>
        </Card>
      )}

      {!searchResults && (
        <Card>
          <div className="px-6 py-4 border-b border-surface-200 dark:border-surface-700">
            <h2 className="font-semibold text-surface-900 dark:text-surface-50">最近のナレッジ</h2>
          </div>
          {isLoadingRecent ? (
            <div className="p-6">
              <div className="animate-pulse space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-16 bg-surface-100 dark:bg-surface-800 rounded" />
                ))}
              </div>
            </div>
          ) : recentItems?.items?.length > 0 ? (
            <div className="divide-y divide-surface-100 dark:divide-surface-800">
              {recentItems.items.map((item: KnowledgeItem) => renderKnowledgeItem(item))}
            </div>
          ) : (
            <div className="p-12 text-center">
              <BookOpen className="w-12 h-12 text-surface-300 dark:text-surface-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-surface-900 dark:text-surface-50 mb-2">
                ナレッジがありません
              </h3>
              <p className="text-surface-500 dark:text-surface-400">
                インタビュー完了後、自動的にナレッジが抽出されます
              </p>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
